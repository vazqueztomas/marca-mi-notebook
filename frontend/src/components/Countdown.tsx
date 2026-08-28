import { useEffect, useState } from 'react'

function timeLeft(endsAt: string) {
  const diff = new Date(endsAt).getTime() - Date.now()
  if (diff <= 0) return null
  const days = Math.floor(diff / 86400000)
  const hours = Math.floor((diff % 86400000) / 3600000)
  const minutes = Math.floor((diff % 3600000) / 60000)
  return { days, hours, minutes }
}

export default function Countdown({ endsAt }: { endsAt: string | null }) {
  const [left, setLeft] = useState(() => (endsAt ? timeLeft(endsAt) : null))

  useEffect(() => {
    if (!endsAt) return
    setLeft(timeLeft(endsAt))
    const interval = setInterval(() => setLeft(timeLeft(endsAt)), 60_000)
    return () => clearInterval(interval)
  }, [endsAt])

  if (!left) return null

  return (
    <span>
      La subasta termina en {left.days}d {left.hours}h {left.minutes}m
    </span>
  )
}
