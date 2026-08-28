from database import get_transaction
from config import get_settings
from loguru import logger
from services.mercadopago import mp_service
from services.mail import mail_service
import psycopg2

settings = get_settings()


def process_payment_webhook(payment_id: str, preference_id: str) -> dict:
    """
    Process Mercado Pago payment confirmation with row-level locking.

    Flow:
    1. Fetch full payment details from MP API
    2. Get the bid by mp_preference_id
    3. Lock the spot row (SELECT ... FOR UPDATE) to serialize concurrent confirmations
    4. Check if this bid is the highest among paid bids for the spot
    5. If yes: mark as paid, refund previous winner, send email
    6. If no: refund this bid, mark outbid_refunded, send email

    Idempotency: mp_payment_id is UNIQUE — retrying the same payment is a no-op.

    Returns: {"status": "paid" | "outbid_refunded" | "already_processed" | "error", "message": str}
    """

    # Fetch full payment from MP API
    try:
        payment = mp_service.get_payment(payment_id)
    except Exception as e:
        logger.error(f"Failed to fetch payment {payment_id}: {e}")
        return {"status": "error", "message": f"Payment fetch failed: {e}"}

    payment_status = payment.get("status")
    amount = payment.get("transaction_amount", 0)
    external_reference = payment.get("external_reference", "")

    # MP webhook may fire multiple times; only process approved payments
    if payment_status != "approved":
        logger.info(f"Payment {payment_id} status {payment_status}, ignoring")
        return {"status": "ignored", "message": f"Payment status {payment_status} is not approved"}

    with get_transaction() as conn:
        with conn.cursor() as cur:
            # Step 1: Get bid by preference_id
            cur.execute("""
            SELECT id, spot_id, bidder_name, bidder_email, amount_ars, status
            FROM bids
            WHERE mp_preference_id = %s
            """, (preference_id,))

            bid_row = cur.fetchone()
            if not bid_row:
                logger.warning(f"Bid not found for preference {preference_id}")
                return {"status": "error", "message": "Bid not found"}

            bid_id = bid_row[0]
            spot_id = bid_row[1]
            bidder_name = bid_row[2]
            bidder_email = bid_row[3]
            bid_amount = bid_row[4]
            bid_status = bid_row[5]

            # Step 2: Idempotency check via mp_payment_id UNIQUE constraint
            # If this bid already has an mp_payment_id (different from current), it's been processed
            if bid_status in ['paid', 'outbid_refunded', 'rejected_refunded', 'refund_failed']:
                logger.info(f"Bid {bid_id} already processed as {bid_status}, skipping")
                return {"status": "already_processed", "message": f"Bid already {bid_status}"}

            # Try to insert the payment_id; if UNIQUE constraint fails, it's a retry
            try:
                cur.execute("""
                UPDATE bids
                SET mp_payment_id = %s
                WHERE id = %s AND mp_payment_id IS NULL
                """, (payment_id, bid_id))

                if cur.rowcount == 0:
                    # mp_payment_id already set — this is a retry
                    cur.execute("SELECT mp_payment_id FROM bids WHERE id = %s", (bid_id,))
                    existing_payment = cur.fetchone()
                    if existing_payment and existing_payment[0] == payment_id:
                        logger.info(f"Retry of payment {payment_id} for bid {bid_id}, no-op")
                        return {"status": "already_processed", "message": "Payment already processed"}
                    else:
                        return {"status": "error", "message": "Bid payment mismatch"}
            except psycopg2.IntegrityError as e:
                # UNIQUE constraint on mp_payment_id — retry detection
                conn.rollback()
                logger.info(f"Payment {payment_id} already processed (UNIQUE constraint), no-op")
                return {"status": "already_processed", "message": "Payment already processed"}

            # Step 3: Lock the spot row for serialization
            cur.execute("SELECT id FROM spots WHERE id = %s FOR UPDATE", (spot_id,))

            # Step 4: Get current highest paid bid for this spot
            cur.execute("""
            SELECT id, bidder_email, bidder_name, amount_ars
            FROM bids
            WHERE spot_id = %s AND status = 'paid'
            ORDER BY amount_ars DESC
            LIMIT 1
            """, (spot_id,))

            current_winner_row = cur.fetchone()
            current_highest_amount = current_winner_row[3] if current_winner_row else 0

            # Step 5a: Is this new bid higher than current highest?
            if bid_amount > current_highest_amount:
                logger.info(f"Bid {bid_id} wins with amount {bid_amount} > {current_highest_amount}")

                # Mark this bid as paid
                cur.execute("""
                UPDATE bids
                SET status = 'paid', updated_at = NOW()
                WHERE id = %s
                """, (bid_id,))

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
                    try:
                        # Extract payment_id from previous bid if available
                        cur.execute("SELECT mp_payment_id FROM bids WHERE id = %s", (prev_bid_id,))
                        prev_payment = cur.fetchone()
                        if prev_payment and prev_payment[0]:
                            mp_service.create_refund(prev_payment[0])
                    except Exception as e:
                        logger.error(f"Refund failed for previous bid {prev_bid_id}: {e}")
                        # Mark refund as failed but don't crash
                        cur.execute("""
                        UPDATE bids
                        SET status = 'refund_failed', updated_at = NOW()
                        WHERE id = %s
                        """, (prev_bid_id,))

                    # Send "you've been outbid" email to previous winner
                    try:
                        # Get spot name for email
                        cur.execute("SELECT position_name FROM spots WHERE id = %s", (spot_id,))
                        spot = cur.fetchone()
                        spot_name = spot[0] if spot else f"Spot {spot_id}"
                        mail_service.send_outbid_email(prev_email, prev_name, spot_name, prev_amount)
                    except Exception as e:
                        logger.error(f"Failed to send outbid email to {prev_email}: {e}")

                return {"status": "paid", "message": f"Bid {bid_id} marked as paid, previous winner refunded"}

            # Step 5b: This bid is not the highest — refund immediately
            else:
                logger.info(f"Bid {bid_id} (${bid_amount}) is outbid by existing bid (${current_highest_amount})")

                # Mark as outbid_refunded
                cur.execute("""
                UPDATE bids
                SET status = 'outbid_refunded', updated_at = NOW()
                WHERE id = %s
                """, (bid_id,))

                # Attempt refund via MP
                try:
                    mp_service.create_refund(payment_id)
                except Exception as e:
                    logger.error(f"Refund failed for outbid bid {bid_id}: {e}")
                    # Mark refund as failed but don't crash
                    cur.execute("""
                    UPDATE bids
                    SET status = 'refund_failed', updated_at = NOW()
                    WHERE id = %s
                    """, (bid_id,))

                # Send "you've been outbid" email
                try:
                    cur.execute("SELECT position_name FROM spots WHERE id = %s", (spot_id,))
                    spot = cur.fetchone()
                    spot_name = spot[0] if spot else f"Spot {spot_id}"
                    mail_service.send_outbid_email(bidder_email, bidder_name, spot_name, bid_amount)
                except Exception as e:
                    logger.error(f"Failed to send outbid email to {bidder_email}: {e}")

                return {"status": "outbid_refunded", "message": f"Bid {bid_id} is lower, refund issued"}
