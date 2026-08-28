import { useState, useEffect } from 'react'
import { metaAPI } from '../api'

export function useMeta() {
  const [auctionEndsAt, setAuctionEndsAt] = useState<string | null>(null)
  const [arsPerUsd, setArsPerUsd] = useState(1000)

  useEffect(() => {
    metaAPI.getMeta().then(({ data }) => {
      setAuctionEndsAt(data.auction_ends_at)
      setArsPerUsd(data.ars_per_usd)
    })
  }, [])

  return { auctionEndsAt, arsPerUsd }
}
