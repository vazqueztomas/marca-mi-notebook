import { useState } from 'react'
import type { Spot } from '../types'
import BidModal from './BidModal'
import { useCurrency } from '../context/CurrencyContext'

interface SpotsGridProps {
  spots: Spot[]
  onRefresh: () => void
}

export default function SpotsGrid({ spots, onRefresh }: SpotsGridProps) {
  const [selectedSpot, setSelectedSpot] = useState<Spot | null>(null)
  const { format } = useCurrency()

  return (
    <>
      <div
        className="relative w-full rounded-2xl p-2 sm:p-4 bg-surface border border-border"
        style={{ aspectRatio: '1.44 / 1' }}
      >
        <div className="absolute inset-0 rounded-[inherit] pointer-events-none"
             style={{
               background: 'radial-gradient(120% 90% at 30% 0%, rgba(255,255,255,0.55) 0%, rgba(255,255,255,0.12) 42%, transparent 70%)'
             }}
        />

        <div className="relative z-10 grid h-full gap-2 p-2 sm:gap-3 sm:p-4"
             style={{
               gridTemplateColumns: 'repeat(6, minmax(0, 1fr))',
               gridTemplateRows: 'minmax(0, 1fr) minmax(0, 0.9fr) minmax(0, 1fr)'
             }}
        >
          {spots.map((spot) => (
            <button
              key={spot.id}
              onClick={() => setSelectedSpot(spot)}
              className="group relative flex items-center justify-center overflow-hidden rounded-xl border border-dashed border-[rgba(0,0,0,0.25)] bg-[rgba(0,0,0,0.02)] hover:border-[rgba(0,0,0,0.45)] transition-colors"
              style={{ gridArea: spot.grid_area }}
            >
              <div className="flex flex-col items-center justify-center gap-1 px-2 py-1 w-full h-full">
                {spot.winning_bid?.logo_url && (
                  <img
                    src={spot.winning_bid.logo_url}
                    alt={spot.winning_bid.bidder_name}
                    className="max-w-[88%] max-h-[55%] object-contain"
                  />
                )}
                {spot.winning_bid && (
                  <span className="text-[10px] sm:text-xs font-semibold leading-tight truncate max-w-full">
                    {spot.winning_bid.bidder_name}
                  </span>
                )}
                <span className="text-[9px] sm:text-[11px] font-medium text-ink-soft">
                  {spot.winning_bid ? format(spot.winning_bid.amount_ars) : 'Libre'}
                </span>
                <span className="text-[9px] sm:text-[11px] font-semibold text-celeste">
                  Superar →
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {selectedSpot && (
        <BidModal
          spot={selectedSpot}
          onClose={() => setSelectedSpot(null)}
          onSuccess={() => {
            setSelectedSpot(null)
            onRefresh()
          }}
        />
      )}
    </>
  )
}
