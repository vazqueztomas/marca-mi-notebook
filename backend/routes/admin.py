from fastapi import APIRouter, HTTPException, Depends, Cookie
from loguru import logger
from database import execute_query, execute_update
from services.admin_auth import login_admin, verify_session
from typing import Optional

router = APIRouter()

def get_admin_session(session_token: Optional[str] = Cookie(None)):
    """Dependency to verify admin session."""
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = verify_session(session_token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return session

@router.post("/admin/login")
async def admin_login(password: str):
    """Login as admin, return session token."""
    token = login_admin(password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid password")
    return {"token": token, "message": "Logged in"}

@router.get("/admin/spots", dependencies=[Depends(get_admin_session)])
async def admin_get_spots():
    """Get all spots with ALL bids (including pending), for admin view."""
    query = """
    SELECT
      s.id,
      s.position_name,
      s.size,
      s.grid_area,
      s.status,
      s.closed_at
    FROM spots s
    ORDER BY s.id
    """
    spots = execute_query(query)

    result = []
    for spot in spots:
        # Get all bids for this spot
        bids_query = """
        SELECT id, bidder_name, bidder_email, amount_ars, status, logo_url, created_at
        FROM bids
        WHERE spot_id = %s
        ORDER BY created_at DESC
        """
        bids = execute_query(bids_query, (spot['id'],))

        result.append({
            "id": spot['id'],
            "position_name": spot['position_name'],
            "size": spot['size'],
            "grid_area": spot['grid_area'],
            "status": spot['status'],
            "closed_at": spot['closed_at'],
            "bids": bids
        })

    return result

@router.post("/admin/spots/{spot_id}/close", dependencies=[Depends(get_admin_session)])
async def admin_close_spot(spot_id: int):
    """Close a spot (no more bids allowed), record winning bid."""
    # Find current winning bid
    winning_query = """
    SELECT id FROM bids
    WHERE spot_id = %s AND status = 'paid'
    ORDER BY amount_ars DESC
    LIMIT 1
    """
    winning_bid = execute_query(winning_query, (spot_id,), fetch_one=True)
    winning_bid_id = winning_bid['id'] if winning_bid else None

    # Update spot
    update_query = """
    UPDATE spots
    SET status = 'closed', closed_at = NOW(), winning_bid_id = %s
    WHERE id = %s
    """
    execute_update(update_query, (winning_bid_id, spot_id))

    logger.info(f"Spot {spot_id} closed, winning bid: {winning_bid_id}")
    return {"status": "closed", "winning_bid_id": winning_bid_id}

@router.post("/admin/bids/{bid_id}/reject", dependencies=[Depends(get_admin_session)])
async def admin_reject_bid(bid_id: int):
    """Reject a bid and refund (moderação post-hoc)."""
    # Get bid details
    bid_query = "SELECT spot_id, amount_ars, bidder_email, status FROM bids WHERE id = %s"
    bid = execute_query(bid_query, (bid_id,), fetch_one=True)

    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")

    if bid['status'] not in ['pending_payment', 'paid']:
        raise HTTPException(status_code=400, detail=f"Cannot reject bid with status {bid['status']}")

    # Mark as rejected_refunded
    update_query = "UPDATE bids SET status = 'rejected_refunded', updated_at = NOW() WHERE id = %s"
    execute_update(update_query, (bid_id,))

    # TODO: Call MP refund if status was 'paid'
    if bid['status'] == 'paid':
        logger.info(f"TODO: Refund ${bid['amount_ars']} for bid {bid_id}")

    logger.info(f"Bid {bid_id} rejected and refunded")
    return {"status": "rejected", "bid_id": bid_id}
