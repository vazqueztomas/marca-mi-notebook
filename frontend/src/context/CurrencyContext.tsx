import { createContext, useContext, useState, useMemo, type ReactNode } from 'react'

interface CurrencyContextValue {
  currency: 'ARS' | 'USD'
  toggle: () => void
  format: (amountArs: number) => string
}

const CurrencyContext = createContext<CurrencyContextValue | null>(null)

export function CurrencyProvider({ arsPerUsd, children }: { arsPerUsd: number; children: ReactNode }) {
  const [currency, setCurrency] = useState<'ARS' | 'USD'>('ARS')

  const value = useMemo<CurrencyContextValue>(() => ({
    currency,
    toggle: () => setCurrency((c) => (c === 'ARS' ? 'USD' : 'ARS')),
    format: (amountArs: number) =>
      currency === 'ARS'
        ? `$${amountArs.toLocaleString('es-AR')}`
        : `US$${Math.round(amountArs / arsPerUsd).toLocaleString('en-US')}`,
  }), [currency, arsPerUsd])

  return <CurrencyContext.Provider value={value}>{children}</CurrencyContext.Provider>
}

export function useCurrency() {
  const ctx = useContext(CurrencyContext)
  if (!ctx) throw new Error('useCurrency must be used within CurrencyProvider')
  return ctx
}
