from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from loguru import logger
from database import execute_query, execute_update
from services.storage import storage_client
from services.mercadopago import mp_service

router = APIRouter()

# Allowed image types and max size for logo uploads
ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


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
    1. Validate file upload (type, size)
    2. Validate spot is open
    3. Validate amount > current highest paid bid
    4. Upload logo to Supabase
    5. Create bid record (pending_payment)
    6. Create MP preference
    7. Return checkout_url
    """

    # 1. Validate file upload
    if logo.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}"
        )

    logo_bytes = await logo.read()
    if len(logo_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024:.0f}MB"
        )

    # 2. Verify spot exists and is open
    spot_query = "SELECT id, status FROM spots WHERE id = %s"
    spot = execute_query(spot_query, (spot_id,), fetch_one=True)

    if not spot:
        raise HTTPException(status_code=404, detail="Spot not found")

    if spot['status'] == 'closed':
        raise HTTPException(status_code=400, detail="Spot is closed")

    # 3. Verify amount > highest paid bid
    current_bid_query = """
    SELECT MAX(amount_ars) as max_amount
    FROM bids
    WHERE spot_id = %s AND status = 'paid'
    """
    current_bid = execute_query(current_bid_query, (spot_id,), fetch_one=True)
    highest_paid = (current_bid or {}).get('max_amount') or 0

    if amount_ars <= highest_paid:
        raise HTTPException(
            status_code=400,
            detail=f"Bid amount (${amount_ars}) must be higher than current bid (${highest_paid})"
        )

    # 4. Upload logo
    logo_url = await storage_client.upload_logo(logo_bytes, logo.filename)

    # 5. Create bid record
    insert_bid_query = """
    INSERT INTO bids (spot_id, bidder_name, bidder_email, logo_url, amount_ars, status, created_at, updated_at)
    VALUES (%s, %s, %s, %s, %s, 'pending_payment', NOW(), NOW())
    RETURNING id
    """
    result = execute_query(insert_bid_query, (spot_id, bidder_name, bidder_email, logo_url, amount_ars))
    bid_db_id = result[0]['id']

    # 6. Create MP preference
    try:
        preference_id, checkout_url = mp_service.create_preference(
            bid_id=bid_db_id,
            spot_id=spot_id,
            amount_ars=amount_ars,
            bidder_email=bidder_email,
            bidder_name=bidder_name
        )
    except Exception as e:
        logger.error(f"Failed to create MP preference for bid {bid_db_id}: {e}")
        logger.warning(f"Deleted orphaned bid {bid_db_id}: MP preference creation failed")
        execute_update("DELETE FROM bids WHERE id = %s", (bid_db_id,))
        raise HTTPException(status_code=500, detail="Payment setup failed")

    # 7. Update bid with preference_id
    update_pref_query = "UPDATE bids SET mp_preference_id = %s WHERE id = %s"
    execute_update(update_pref_query, (preference_id, bid_db_id))

    logger.info(f"Bid created: {bid_db_id}, redirect to {checkout_url}")

    return {
        "bid_id": bid_db_id,
        "preference_id": preference_id,
        "checkout_url": checkout_url
    }
