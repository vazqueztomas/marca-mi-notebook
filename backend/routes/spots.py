from fastapi import APIRouter, HTTPException
from loguru import logger
from database import execute_query
from schemas import SpotsResponseSchema, SpotDetailSchema, BidHistorySchema

router = APIRouter()


@router.get("/spots", response_model=SpotsResponseSchema)
async def get_spots():
    """Get all 10 spots with their current winning bid and bid count."""
    query = """
    SELECT
      s.id,
      s.position_name,
      s.size,
      s.grid_area,
      s.status,
      (SELECT b.id FROM bids b
       WHERE b.spot_id = s.id
       AND b.status = 'paid'
       ORDER BY b.amount_ars DESC, b.id ASC
       LIMIT 1) as winning_bid_id
    FROM spots s
    ORDER BY s.id
    """
    spots_rows = execute_query(query)

    spots = []
    raised_total = 0

    for row in spots_rows:
        # Get winning bid details if exists
        winning_bid = None
        bid_count = 0

        if row['winning_bid_id']:
            bid_query = """
            SELECT bidder_name, amount_ars, logo_url
            FROM bids
            WHERE id = %s
            """
            bid_row = execute_query(bid_query, (row['winning_bid_id'],), fetch_one=True)
            if bid_row:
                winning_bid = {
                    "bidder_name": bid_row['bidder_name'],
                    "amount_ars": bid_row['amount_ars'],
                    "logo_url": bid_row['logo_url']
                }
                raised_total += bid_row['amount_ars']

        # Get bid count
        count_query = "SELECT COUNT(*) as cnt FROM bids WHERE spot_id = %s AND status IN ('paid', 'outbid_refunded')"
        count_row = execute_query(count_query, (row['id'],), fetch_one=True)
        bid_count = count_row['cnt'] if count_row else 0

        spots.append({
            "id": row['id'],
            "position_name": row['position_name'],
            "size": row['size'],
            "grid_area": row['grid_area'],
            "status": row['status'],
            "winning_bid": winning_bid,
            "bid_count": bid_count
        })

    return {"raised_total": raised_total, "spots": spots}


@router.get("/spots/{spot_id}/bids", response_model=SpotDetailSchema)
async def get_spot_bids(spot_id: int):
    """Get a spot and its bid history."""
    query = "SELECT id, position_name, size, status FROM spots WHERE id = %s"
    spot = execute_query(query, (spot_id,), fetch_one=True)

    if not spot:
        raise HTTPException(status_code=404, detail="Spot not found")

    bids_query = """
    SELECT id, bidder_name, amount_ars, status, created_at
    FROM bids
    WHERE spot_id = %s
    ORDER BY created_at DESC
    """
    bids = execute_query(bids_query, (spot_id,))

    return {
        "id": spot['id'],
        "position_name": spot['position_name'],
        "size": spot['size'],
        "status": spot['status'],
        "bids": [
            {
                "id": b['id'],
                "bidder_name": b['bidder_name'],
                "amount_ars": b['amount_ars'],
                "status": b['status'],
                "created_at": b['created_at']
            }
            for b in bids
        ]
    }
