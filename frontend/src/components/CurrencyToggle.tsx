import { useCurrency } from '../context/CurrencyContext'

export default function CurrencyToggle() {
  const { currency, toggle } = useCurrency()

  return (
    <button
      onClick={toggle}
      className="text-xs font-semibold px-3 py-1.5 rounded-full border border-border bg-surface hover:bg-surface-2 transition-colors"
      title="Cambiar moneda"
    >
      {currency === 'ARS' ? '$ ARS' : 'US$'}
    </button>
  )
}
