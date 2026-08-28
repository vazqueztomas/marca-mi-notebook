from fastapi import APIRouter, Request, HTTPException
from loguru import logger
from services.bid_engine import process_payment_webhook

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

    We extract payment_id, fetch full payment details from MP API,
    then process the bid workflow with locking and refund logic.
    """

    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook body: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    action = body.get("action")
    payment_id = body.get("data", {}).get("id")

    if not payment_id:
        logger.warning("Webhook received without payment_id, ignoring")
        return {"status": "ignored"}

    logger.info(f"Webhook received: action={action}, payment_id={payment_id}")

    # Process the payment — fetch preference_id and status from MP API
    try:
        from services.mercadopago import mp_service

        payment = mp_service.get_payment(payment_id)
        preference_id = payment.get("preference_id")

        if not preference_id:
            logger.warning(f"Payment {payment_id} has no preference_id, ignoring")
            return {"status": "ignored"}

        result = process_payment_webhook(payment_id, preference_id)
        return {"status": result["status"], "message": result["message"]}

    except Exception as e:
        logger.error(f"Webhook processing failed for payment {payment_id}: {e}")
        # Return 200 to acknowledge to MP, but log the error
        return {"status": "error", "message": str(e)}
