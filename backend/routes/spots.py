from fastapi import APIRouter, HTTPException
from loguru import logger
from database import execute_query
from schemas import SpotsResponseSchema, SpotDetailSchema, BidHistorySchema

router = APIRouter()


@router.get("/spots", response_model=SpotsResponseSchema)
async def get_spots():
    """Get all 10 spots with their current winning bid and bid count — one round trip."""
    query = """
    SELECT
      s.id,
      s.position_name,
      s.size,
      s.grid_area,
      s.status,
      w.bidder_name AS winning_bidder_name,
      w.amount_ars AS winning_amount_ars,
      w.logo_url AS winning_logo_url,
      COALESCE(c.cnt, 0) AS bid_count
    FROM spots s
    LEFT JOIN LATERAL (
      SELECT bidder_name, amount_ars, logo_url
      FROM bids b
      WHERE b.spot_id = s.id AND b.status = 'paid'
      ORDER BY b.amount_ars DESC, b.id ASC
      LIMIT 1
    ) w ON true
    LEFT JOIN LATERAL (
      SELECT COUNT(*) AS cnt
      FROM bids b
      WHERE b.spot_id = s.id AND b.status IN ('paid', 'outbid_refunded')
    ) c ON true
    ORDER BY s.id
    """
    spots_rows = execute_query(query)

    spots = []
    raised_total = 0

    for row in spots_rows:
        winning_bid = None
        if row['winning_bidder_name'] is not None:
            winning_bid = {
                "bidder_name": row['winning_bidder_name'],
                "amount_ars": row['winning_amount_ars'],
                "logo_url": row['winning_logo_url']
            }
            raised_total += row['winning_amount_ars']

        spots.append({
            "id": row['id'],
            "position_name": row['position_name'],
            "size": row['size'],
            "grid_area": row['grid_area'],
            "status": row['status'],
            "winning_bid": winning_bid,
            "bid_count": row['bid_count']
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
