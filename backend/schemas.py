from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class WinningBidSchema(BaseModel):
    bidder_name: str
    amount_ars: int
    logo_url: Optional[str]


class SpotSchema(BaseModel):
    id: int
    position_name: str
    size: str
    grid_area: str
    status: str
    winning_bid: Optional[WinningBidSchema]
    bid_count: int

    class Config:
        from_attributes = True


class SpotsResponseSchema(BaseModel):
    raised_total: int
    spots: list[SpotSchema]


class BidHistorySchema(BaseModel):
    id: int
    bidder_name: str
    amount_ars: int
    status: str
    created_at: datetime


class SpotDetailSchema(BaseModel):
    id: int
    position_name: str
    size: str
    status: str
    bids: list[BidHistorySchema]
