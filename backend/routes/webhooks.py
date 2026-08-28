from fastapi import APIRouter, Request, HTTPException
from fastapi.concurrency import run_in_threadpool
from loguru import logger
from services.bid_engine import process_payment_webhook
from services.mercadopago import mp_service

router = APIRouter()


@router.post("/webhooks/mercadopago")
async def mercadopago_webhook(request: Request):
    """
    Handle Mercado Pago webhook notifications.

    MP sends:
    {
      "action": "payment.created",
      "data": {
        "id": "payment_id"
      }
    }

    We fetch full payment details from MP API using payment_id,
    then pass the payment object to bid_engine for processing.

    Returns 500 if payment fetch fails (so MP retries).
    Returns 200 after any state change (idempotent).
    """

    try:
        body_dict = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook body: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    action = body_dict.get("action")
    payment_id = body_dict.get("data", {}).get("id")

    if not payment_id:
        logger.warning("Webhook received without payment_id, ignoring")
        return {"status": "ignored"}

    logger.info(f"Webhook received: action={action}, payment_id={payment_id}")

    # Fetch full payment from MP API — if this fails, return 500 so MP retries
    try:
        payment = await run_in_threadpool(mp_service.get_payment, payment_id)
    except Exception as e:
        logger.error(f"Failed to fetch payment {payment_id} from MP: {e}")
        raise HTTPException(status_code=500, detail="Payment fetch failed")

    # Process the payment with locking logic
    try:
        result = await run_in_threadpool(process_payment_webhook, payment)
        # Always return 200 after fetching payment (idempotent, state changes logged)
        return {"status": result["status"], "message": result["message"]}
    except Exception as e:
        logger.error(f"Webhook processing failed for payment {payment_id}: {e}")
        # Return 200 even on processing errors (bid_engine handles all state cases)
        return {"status": "error", "message": str(e)}
