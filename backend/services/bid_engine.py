from database import get_transaction
from config import get_settings
from loguru import logger
from services.mercadopago import mp_service
from services.mail import mail_service
import psycopg2

settings = get_settings()


def process_payment_webhook(payment: dict) -> dict:
    """
    Process Mercado Pago payment confirmation with row-level locking.

    Flow:
    1. Extract bid_id from payment["external_reference"]
    2. Get the bid and lock the spot row (SELECT ... FOR UPDATE)
    3. Validate transaction_amount matches bid's amount_ars
    4. Check if this bid is the highest among paid bids for the spot
    5. If yes: mark as paid, refund previous winner, send email only if refund succeeds
    6. If no: refund this bid, mark outbid_refunded, send email only if refund succeeds

    Idempotency: mp_payment_id is UNIQUE — retrying the same payment is a no-op.

    Returns: {"status": "paid" | "outbid_refunded" | "already_processed" | "error", "message": str}
    """

    payment_id = str(payment.get("id"))  # MP returns id as int; mp_payment_id is VARCHAR
    external_reference = payment.get("external_reference", "")
    payment_status = payment.get("status")
    transaction_amount = payment.get("transaction_amount", 0)

    # Only process approved payments
    if payment_status != "approved":
        logger.info(f"Payment {payment_id} status {payment_status}, ignoring")
        return {"status": "ignored", "message": f"Payment status {payment_status} is not approved"}

    # Extract bid_id from external_reference
    try:
        bid_id = int(external_reference)
    except (ValueError, TypeError):
        logger.error(f"Invalid external_reference {external_reference} for payment {payment_id}")
        return {"status": "error", "message": f"Invalid bid reference in payment"}

    with get_transaction() as conn:
        with conn.cursor() as cur:
            # Step 1: Get bid by id
            cur.execute("""
            SELECT id, spot_id, bidder_name, bidder_email, amount_ars, status
            FROM bids
            WHERE id = %s
            """, (bid_id,))

            bid_row = cur.fetchone()
            if not bid_row:
                logger.warning(f"Bid {bid_id} not found for payment {payment_id}")
                return {"status": "error", "message": "Bid not found"}

            bid_db_id = bid_row[0]
            spot_id = bid_row[1]
            bidder_name = bid_row[2]
            bidder_email = bid_row[3]
            bid_amount = bid_row[4]
            bid_status = bid_row[5]

            # Step 2: Idempotency check via status
            if bid_status in ['paid', 'outbid_refunded', 'rejected_refunded', 'refund_failed']:
                logger.info(f"Bid {bid_db_id} already processed as {bid_status}, skipping")
                return {"status": "already_processed", "message": f"Bid already {bid_status}"}

            # Attempt to set mp_payment_id; if UNIQUE constraint fails, it's a retry
            try:
                cur.execute("""
                UPDATE bids
                SET mp_payment_id = %s
                WHERE id = %s AND mp_payment_id IS NULL
                """, (payment_id, bid_db_id))

                if cur.rowcount == 0:
                    # mp_payment_id already set — this is a retry or different payment claimed this bid
                    cur.execute("SELECT mp_payment_id FROM bids WHERE id = %s", (bid_db_id,))
                    existing_payment = cur.fetchone()
                    if existing_payment and existing_payment[0] == payment_id:
                        logger.info(f"Retry of payment {payment_id} for bid {bid_db_id}, no-op")
                        return {"status": "already_processed", "message": "Payment already processed"}
                    elif existing_payment and existing_payment[0]:
                        # Different payment already claimed this bid — refund the current payment
                        logger.warning(f"Bid {bid_db_id} already claimed by payment {existing_payment[0]}, refunding payment {payment_id}")
                        try:
                            mp_service.create_refund(payment_id)
                        except Exception as e:
                            logger.error(f"Failed to refund duplicate payment {payment_id}: {e}")
                        return {"status": "error", "message": "Bid already claimed by different payment"}
            except psycopg2.IntegrityError:
                # UNIQUE constraint on mp_payment_id — this payment is already in the system
                conn.rollback()
                logger.info(f"Payment {payment_id} already processed (UNIQUE constraint), no-op")
                return {"status": "already_processed", "message": "Payment already processed"}

            # Step 3: Validate money amount
            if int(transaction_amount) != bid_amount:
                logger.error(f"Amount mismatch: payment ${transaction_amount} vs bid ${bid_amount} for bid {bid_db_id}")
                # Refund the payment and mark bid as rejected
                try:
                    mp_service.create_refund(payment_id)
                except Exception as e:
                    logger.error(f"Failed to refund mismatched payment {payment_id}: {e}")
                cur.execute("""
                UPDATE bids
                SET status = 'rejected_refunded', updated_at = NOW()
                WHERE id = %s
                """, (bid_db_id,))
                return {"status": "error", "message": "Payment amount mismatch"}

            # Step 4: Lock the spot row for serialization
            cur.execute("SELECT id FROM spots WHERE id = %s FOR UPDATE", (spot_id,))

            # Step 5: Get current highest paid bid for this spot
            cur.execute("""
            SELECT id, bidder_email, bidder_name, amount_ars
            FROM bids
            WHERE spot_id = %s AND status = 'paid'
            ORDER BY amount_ars DESC
            LIMIT 1
            """, (spot_id,))

            current_winner_row = cur.fetchone()
            current_highest_amount = current_winner_row[3] if current_winner_row else 0

            # Step 6a: Is this new bid higher than current highest?
            if bid_amount > current_highest_amount:
                logger.info(f"Bid {bid_db_id} wins with amount {bid_amount} > {current_highest_amount}")

                # Mark this bid as paid
                cur.execute("""
                UPDATE bids
                SET status = 'paid', updated_at = NOW()
                WHERE id = %s
                """, (bid_db_id,))

                # Refund previous winner if exists
                if current_winner_row:
                    prev_bid_id, prev_email, prev_name, prev_amount = current_winner_row
                    logger.info(f"Refunding previous winner bid {prev_bid_id} (${prev_amount})")

                    # Mark previous bid as outbid_refunded
                    cur.execute("""
                    UPDATE bids
                    SET status = 'outbid_refunded', updated_at = NOW()
                    WHERE id = %s
                    """, (prev_bid_id,))

                    # Attempt refund via MP
                    refund_success = False
                    cur.execute("SELECT mp_payment_id FROM bids WHERE id = %s", (prev_bid_id,))
                    prev_payment = cur.fetchone()
                    try:
                        if prev_payment and prev_payment[0]:
                            mp_service.create_refund(prev_payment[0])
                            refund_success = True
                    except Exception as e:
                        # Only an explicit "already refunded" MP error counts as success
                        if "already refunded" in str(e).lower():
                            logger.info(f"Previous payment {prev_payment[0]} already refunded, treating as success")
                            refund_success = True
                        else:
                            logger.error(f"Refund failed for previous bid {prev_bid_id}: {e}")
                            # Mark refund as failed but don't crash
                            cur.execute("""
                            UPDATE bids
                            SET status = 'refund_failed', updated_at = NOW()
                            WHERE id = %s
                            """, (prev_bid_id,))

                    # Send "you've been outbid" email ONLY if refund succeeded
                    if refund_success:
                        try:
                            # Get spot name for email
                            cur.execute("SELECT position_name FROM spots WHERE id = %s", (spot_id,))
                            spot = cur.fetchone()
                            spot_name = spot[0] if spot else f"Spot {spot_id}"
                            mail_service.send_outbid_email(prev_email, prev_name, spot_name, prev_amount)
                        except Exception as e:
                            logger.error(f"Failed to send outbid email to {prev_email}: {e}")

                return {"status": "paid", "message": f"Bid {bid_db_id} marked as paid"}

            # Step 6b: This bid is not the highest — refund immediately
            else:
                logger.info(f"Bid {bid_db_id} (${bid_amount}) is outbid by existing bid (${current_highest_amount})")

                # Mark as outbid_refunded
                cur.execute("""
                UPDATE bids
                SET status = 'outbid_refunded', updated_at = NOW()
                WHERE id = %s
                """, (bid_db_id,))

                # Attempt refund via MP
                refund_success = False
                try:
                    mp_service.create_refund(payment_id)
                    refund_success = True
                except Exception as e:
                    # Only an explicit "already refunded" MP error counts as success
                    if "already refunded" in str(e).lower():
                        logger.info(f"Payment {payment_id} already refunded, treating as success")
                        refund_success = True
                    else:
                        logger.error(f"Refund failed for outbid bid {bid_db_id}: {e}")
                        # Mark refund as failed but don't crash
                        cur.execute("""
                        UPDATE bids
                        SET status = 'refund_failed', updated_at = NOW()
                        WHERE id = %s
                        """, (bid_db_id,))

                # Send "you've been outbid" email ONLY if refund succeeded
                if refund_success:
                    try:
                        cur.execute("SELECT position_name FROM spots WHERE id = %s", (spot_id,))
                        spot = cur.fetchone()
                        spot_name = spot[0] if spot else f"Spot {spot_id}"
                        mail_service.send_outbid_email(bidder_email, bidder_name, spot_name, bid_amount)
                    except Exception as e:
                        logger.error(f"Failed to send outbid email to {bidder_email}: {e}")

                return {"status": "outbid_refunded", "message": f"Bid {bid_db_id} is lower, refund issued"}
