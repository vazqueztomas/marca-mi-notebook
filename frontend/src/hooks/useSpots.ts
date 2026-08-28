import { useState, useEffect } from 'react'
import { spotsAPI } from '../api'
import type { Spot } from '../types'

export function useSpots() {
  const [spots, setSpots] = useState<Spot[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchSpots = async () => {
      try {
        const { data } = await spotsAPI.getSpots()
        setSpots(data.spots)
        setTotal(data.raised_total)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch spots')
      } finally {
        setLoading(false)
      }
    }

    fetchSpots()
    const interval = setInterval(fetchSpots, 5000) // Poll every 5s

    return () => clearInterval(interval)
  }, [])

  return { spots, total, loading, error }
}
