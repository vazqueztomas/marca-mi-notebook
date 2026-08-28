from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal


@dataclass
class Spot:
    id: int
    position_name: str
    size: Literal["small", "medium", "large"]
    grid_area: str
    status: Literal["open", "closed"]
    closed_at: Optional[datetime] = None
    winning_bid_id: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class Bid:
    id: int
    spot_id: int
    bidder_name: str
    bidder_email: str
    logo_url: Optional[str]
    amount_ars: int
    status: Literal["pending_payment", "paid", "outbid_refunded", "rejected_refunded", "refund_failed"]
    mp_preference_id: Optional[str] = None
    mp_payment_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
