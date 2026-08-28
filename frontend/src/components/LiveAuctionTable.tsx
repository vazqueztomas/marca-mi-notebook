import type { Spot } from '../types'
import { useCurrency } from '../context/CurrencyContext'

const SIZE_LABEL: Record<Spot['size'], string> = {
  small: 'Chico',
  medium: 'Mediano',
  large: 'Grande',
}

export default function LiveAuctionTable({ spots }: { spots: Spot[] }) {
  const { format } = useCurrency()

  return (
    <section className="mt-12">
      <h2 className="text-2xl font-bold mb-6">Subasta en vivo</h2>
      <div className="overflow-x-auto border border-border rounded-lg">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-surface-2">
              <th className="text-left py-2 px-4 font-semibold">Lugar</th>
              <th className="text-left py-2 px-4 font-semibold">Tamaño</th>
              <th className="text-left py-2 px-4 font-semibold">Quién lo tiene</th>
              <th className="text-left py-2 px-4 font-semibold">Oferta actual</th>
              <th className="text-left py-2 px-4 font-semibold">Ofertas</th>
            </tr>
          </thead>
          <tbody>
            {spots.map((spot) => (
              <tr key={spot.id} className="border-t border-border">
                <td className="py-2 px-4">{spot.position_name}</td>
                <td className="py-2 px-4 text-ink-soft">{SIZE_LABEL[spot.size]}</td>
                <td className="py-2 px-4">{spot.winning_bid?.bidder_name || '—'}</td>
                <td className="py-2 px-4 font-semibold">
                  {spot.winning_bid ? format(spot.winning_bid.amount_ars) : 'Sin ofertas'}
                </td>
                <td className="py-2 px-4 text-ink-soft">{spot.bid_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
