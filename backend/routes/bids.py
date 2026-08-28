from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from loguru import logger
from database import execute_query, execute_update
from services.storage import upload_logo_sync
from services.mercadopago import mp_service
import uuid

router = APIRouter()


@router.post("/spots/{spot_id}/bids")
async def create_bid(
    spot_id: int,
    bidder_name: str = Form(...),
    bidder_email: str = Form(...),
    amount_ars: int = Form(...),
    logo: UploadFile = File(...)
):
    """
    Create a bid for a spot:
    1. Validate spot is open
    2. Validate amount > current highest paid bid
    3. Upload logo to Supabase
    4. Create bid record (pending_payment)
    5. Create MP preference
    6. Return checkout_url
    """

    # 1. Verify spot exists and is open
    spot_query = "SELECT id, status FROM spots WHERE id = %s"
    spot = execute_query(spot_query, (spot_id,), fetch_one=True)

    if not spot:
        raise HTTPException(status_code=404, detail="Spot not found")

    if spot['status'] == 'closed':
        raise HTTPException(status_code=400, detail="Spot is closed")

    # 2. Verify amount > highest paid bid
    current_bid_query = """
    SELECT MAX(amount_ars) as max_amount
    FROM bids
    WHERE spot_id = %s AND status = 'paid'
    """
    current_bid = execute_query(current_bid_query, (spot_id,), fetch_one=True)
    highest_paid = current_bid['max_amount'] if current_bid and current_bid['max_amount'] else 0

    if amount_ars <= highest_paid:
        raise HTTPException(
            status_code=400,
            detail=f"Bid amount (${amount_ars}) must be higher than current bid (${highest_paid})"
        )

    # 3. Upload logo
    logo_bytes = await logo.read()
    logo_url = upload_logo_sync(logo_bytes, logo.filename)

    # 4. Create bid record
    bid_id = str(uuid.uuid4())
    insert_bid_query = """
    INSERT INTO bids (spot_id, bidder_name, bidder_email, logo_url, amount_ars, status, created_at, updated_at)
    VALUES (%s, %s, %s, %s, %s, 'pending_payment', NOW(), NOW())
    RETURNING id
    """
    result = execute_query(insert_bid_query, (spot_id, bidder_name, bidder_email, logo_url, amount_ars))
    bid_db_id = result[0]['id']

    # 5. Create MP preference
    try:
        preference_id, checkout_url = mp_service.create_preference(
            spot_id=spot_id,
            amount_ars=amount_ars,
            bidder_email=bidder_email,
            bidder_name=bidder_name
        )
    except Exception as e:
        logger.error(f"Failed to create MP preference for bid {bid_db_id}: {e}")
        raise HTTPException(status_code=500, detail="Payment setup failed")

    # 6. Update bid with preference_id
    update_pref_query = "UPDATE bids SET mp_preference_id = %s WHERE id = %s"
    execute_update(update_pref_query, (preference_id, bid_db_id))

    logger.info(f"Bid created: {bid_db_id}, redirect to {checkout_url}")

    return {
        "bid_id": bid_db_id,
        "preference_id": preference_id,
        "checkout_url": checkout_url
    }
