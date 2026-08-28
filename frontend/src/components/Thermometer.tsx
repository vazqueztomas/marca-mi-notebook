interface ThermometerProps {
  raised: number
  goal?: number
}

export default function Thermometer({ raised, goal = 4850000 }: ThermometerProps) {
  const percent = Math.min((raised / goal) * 100, 100)
  const percentage = Math.round(percent)

  return (
    <div className="bg-surface border border-border rounded-lg p-5 mt-8">
      <div className="flex justify-between items-baseline gap-2 mb-3 flex-wrap">
        <span className="text-lg font-semibold">
          ${raised.toLocaleString('es-AR')} <span className="text-ink-soft text-sm font-normal">recaudados</span>
        </span>
        <span className="text-sm font-semibold text-live">meta superada {percentage}%</span>
      </div>
      <div className="h-2 bg-celeste-soft rounded-full overflow-hidden mb-2">
        <div className="h-full bg-gradient-to-r from-celeste to-live" style={{ width: `${percent}%` }}></div>
      </div>
      <p className="text-xs text-ink-faint">Meta de arranque: $650.000 · seguimos recibiendo ofertas igual</p>
    </div>
  )
}
