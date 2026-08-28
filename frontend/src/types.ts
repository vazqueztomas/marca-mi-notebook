export interface Spot {
  id: number
  position_name: string
  size: 'small' | 'medium' | 'large'
  grid_area: string
  status: 'open' | 'closed'
  winning_bid?: {
    bidder_name: string
    amount_ars: number
    logo_url?: string
  }
  bid_count: number
}

export interface Bid {
  id: number
  spot_id: number
  bidder_name: string
  bidder_email: string
  logo_url?: string
  amount_ars: number
  status: 'pending_payment' | 'paid' | 'outbid_refunded' | 'rejected_refunded' | 'refund_failed'
  created_at: string
}

export interface SpotsResponse {
  raised_total: number
  spots: Spot[]
}
