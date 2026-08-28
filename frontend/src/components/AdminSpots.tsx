import { useState, useEffect } from 'react'
import { adminAPI } from '../api'

interface AdminBid {
  id: number
  bidder_name: string
  bidder_email: string
  amount_ars: number
  status: 'pending_payment' | 'paid' | 'outbid_refunded' | 'rejected_refunded' | 'refund_failed'
  created_at: string
}

interface AdminSpot {
  id: number
  position_name: string
  size: string
  status: 'open' | 'closed'
  bids: AdminBid[]
}

export default function AdminSpots() {
  const [spots, setSpots] = useState<AdminSpot[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actioning, setActioning] = useState<{
    [key: string]: boolean
  }>({})
  const [actionError, setActionError] = useState<{
    [key: string]: string
  }>({})

  useEffect(() => {
    fetchSpots()
  }, [])

  const fetchSpots = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await adminAPI.getSpots()
      setSpots(res.data.spots)
    } catch (err: any) {
      setError('Failed to load spots')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleCloseSpot = async (spotId: number) => {
    const key = `close-${spotId}`
    try {
      setActioning((prev) => ({ ...prev, [key]: true }))
      setActionError((prev) => ({ ...prev, [key]: '' }))
      await adminAPI.closeSpot(spotId)
      // Update spot status locally
      setSpots((prev) =>
        prev.map((spot) =>
          spot.id === spotId ? { ...spot, status: 'closed' } : spot
        )
      )
    } catch (err: any) {
      setActionError((prev) => ({
        ...prev,
        [key]: err.response?.data?.detail || 'Error al cerrar',
      }))
    } finally {
      setActioning((prev) => ({ ...prev, [key]: false }))
    }
  }

  const handleRejectBid = async (bidId: number, spotId: number) => {
    const key = `reject-${bidId}`
    try {
      setActioning((prev) => ({ ...prev, [key]: true }))
      setActionError((prev) => ({ ...prev, [key]: '' }))
      await adminAPI.rejectBid(bidId)
      // Update bid status locally
      setSpots((prev) =>
        prev.map((spot) =>
          spot.id === spotId
            ? {
                ...spot,
                bids: spot.bids.map((bid) =>
                  bid.id === bidId
                    ? { ...bid, status: 'rejected_refunded' }
                    : bid
                ),
              }
            : spot
        )
      )
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Error al rechazar'
      setActionError((prev) => ({
        ...prev,
        [key]: detail,
      }))
      // If refund failed, update bid status to refund_failed
      if (err.response?.status === 400) {
        setSpots((prev) =>
          prev.map((spot) =>
            spot.id === spotId
              ? {
                  ...spot,
                  bids: spot.bids.map((bid) =>
                    bid.id === bidId
                      ? { ...bid, status: 'refund_failed' }
                      : bid
                  ),
                }
              : spot
          )
        )
      }
    } finally {
      setActioning((prev) => ({ ...prev, [key]: false }))
    }
  }

  if (loading) return <div className="p-8">Cargando...</div>

  if (error) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <p className="text-red-500">{error}</p>
        <button
          onClick={fetchSpots}
          className="mt-4 px-4 py-2 bg-ink text-bg rounded hover:opacity-90"
        >
          Reintentar
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {spots.map((spot) => (
        <div key={spot.id} className="mb-8 border border-border rounded">
          <div className="bg-surface p-4 border-b border-border">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-semibold">{spot.position_name}</h3>
                <p className="text-sm text-ink-soft">
                  Tamaño: {spot.size} | Estado: {spot.status}
                </p>
              </div>
              {spot.status === 'open' && (
                <div>
                  {actionError[`close-${spot.id}`] && (
                    <p className="text-red-500 text-xs mb-2">
                      {actionError[`close-${spot.id}`]}
                    </p>
                  )}
                  <button
                    onClick={() => handleCloseSpot(spot.id)}
                    disabled={actioning[`close-${spot.id}`]}
                    className="text-xs bg-ink text-bg px-3 py-1 rounded hover:opacity-90 disabled:opacity-50"
                  >
                    {actioning[`close-${spot.id}`] ? 'Cerrando...' : 'Cerrar'}
                  </button>
                </div>
              )}
            </div>
          </div>

          {spot.bids.length > 0 ? (
            <table className="w-full">
              <thead>
                <tr className="bg-surface-2">
                  <th className="text-left py-2 px-4 text-sm font-semibold">Nombre</th>
                  <th className="text-left py-2 px-4 text-sm font-semibold">Email</th>
                  <th className="text-left py-2 px-4 text-sm font-semibold">Oferta</th>
                  <th className="text-left py-2 px-4 text-sm font-semibold">Estado</th>
                  <th className="text-left py-2 px-4 text-sm font-semibold">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {spot.bids.map((bid) => (
                  <tr key={bid.id} className="border-b border-border">
                    <td className="py-3 px-4">{bid.bidder_name}</td>
                    <td className="py-3 px-4 text-sm text-ink-soft">{bid.bidder_email}</td>
                    <td className="py-3 px-4">
                      ${bid.amount_ars.toLocaleString('es-AR')}
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-xs bg-surface px-2 py-1 rounded">
                        {bid.status}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      {bid.status === 'pending_payment' && (
                        <div>
                          {actionError[`reject-${bid.id}`] && (
                            <p className="text-red-500 text-xs mb-1">
                              {actionError[`reject-${bid.id}`]}
                            </p>
                          )}
                          <button
                            onClick={() => handleRejectBid(bid.id, spot.id)}
                            disabled={actioning[`reject-${bid.id}`]}
                            className="text-xs text-celeste hover:underline disabled:opacity-50"
                          >
                            {actioning[`reject-${bid.id}`]
                              ? 'Rechazando...'
                              : 'Rechazar'}
                          </button>
                        </div>
                      )}
                      {bid.status === 'refund_failed' && (
                        <span className="text-xs text-red-500">Refund failed</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-4 text-center text-ink-soft text-sm">
              Sin ofertas
            </div>
          )}
        </div>
      ))}

      {spots.length === 0 && (
        <div className="text-center text-ink-soft">
          No hay spots disponibles
        </div>
      )}
    </div>
  )
}
