import { useState, useEffect } from 'react'
import { spotsAPI } from '../api'
import type { Bid } from '../types'

export function useBids(spotId: number) {
  const [bids, setBids] = useState<Bid[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchBids = async () => {
      try {
        const { data } = await spotsAPI.getBids(spotId)
        setBids(data.bids)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch bids')
      } finally {
        setLoading(false)
      }
    }

    fetchBids()
    const interval = setInterval(fetchBids, 5000)

    return () => clearInterval(interval)
  }, [spotId])

  return { bids, loading, error }
}
