import { useState } from 'react'
import { spotsAPI } from '../api'
import type { Spot } from '../types'
import { useCurrency } from '../context/CurrencyContext'

interface BidModalProps {
  spot: Spot
  onClose: () => void
  onSuccess: () => void
}

export default function BidModal({ spot, onClose, onSuccess }: BidModalProps) {
  const [formData, setFormData] = useState({
    bidder_name: '',
    bidder_email: '',
    amount_ars: '',
    logo: null as File | null,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { format } = useCurrency()

  const currentHighest = spot.winning_bid?.amount_ars || 0
  const minBid = currentHighest + 1000 // Min increment ARS 1000

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const fd = new FormData()
      fd.append('bidder_name', formData.bidder_name)
      fd.append('bidder_email', formData.bidder_email)
      fd.append('amount_ars', formData.amount_ars)
      if (formData.logo) {
        fd.append('logo', formData.logo)
      }

      const { data } = await spotsAPI.createBid(spot.id, fd)

      // Redirect to Mercado Pago checkout
      onSuccess()
      window.location.href = data.checkout_url
    } catch (err: any) {
      setError(err.response?.data?.detail || 'No se pudo crear la oferta')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-bg rounded-lg p-6 max-w-md w-full">
        <h2 className="text-2xl font-bold mb-4">{spot.position_name}</h2>

        {spot.winning_bid && (
          <p className="text-sm text-ink-faint mb-4">
            Va ganando: {spot.winning_bid.bidder_name} con {format(spot.winning_bid.amount_ars)}
          </p>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            placeholder="Tu nombre o marca"
            required
            value={formData.bidder_name}
            onChange={(e) => setFormData({ ...formData, bidder_name: e.target.value })}
            className="w-full px-3 py-2 border border-border rounded"
          />
          <input
            type="email"
            placeholder="Tu email"
            required
            value={formData.bidder_email}
            onChange={(e) => setFormData({ ...formData, bidder_email: e.target.value })}
            className="w-full px-3 py-2 border border-border rounded"
          />
          <input
            type="number"
            placeholder={`Oferta mínima: $${minBid.toLocaleString('es-AR')}`}
            required
            min={minBid}
            value={formData.amount_ars}
            onChange={(e) => setFormData({ ...formData, amount_ars: e.target.value })}
            className="w-full px-3 py-2 border border-border rounded"
          />
          <input
            type="file"
            accept="image/*"
            required
            onChange={(e) => setFormData({ ...formData, logo: e.target.files?.[0] || null })}
            className="w-full px-3 py-2 border border-border rounded"
          />

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-ink text-bg font-semibold py-2 rounded hover:opacity-90 disabled:opacity-50"
          >
            {loading ? 'Procesando...' : 'Ir a pagar'}
          </button>
        </form>

        <button
          onClick={onClose}
          className="mt-4 w-full text-center text-ink-soft hover:text-ink"
        >
          Cancelar
        </button>
      </div>
    </div>
  )
}
