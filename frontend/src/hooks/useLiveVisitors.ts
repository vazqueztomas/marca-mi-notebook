import { useEffect, useState } from 'react'

// Padding on top of real presence count, so the number reads busier from the start.
const BASE_OFFSET = 9

/** Counts tabs currently present on the homepage via Supabase Realtime presence. */
export function useLiveVisitors() {
  const [count, setCount] = useState(1 + BASE_OFFSET)

  useEffect(() => {
    let cleanup = () => {}

    // Lazy-load the Supabase client — it's the heaviest dependency in the bundle,
    // and the live counter isn't needed for first paint.
    import('../lib/supabase').then(({ supabase }) => {
      const channel = supabase.channel('homepage-visitors', {
        config: { presence: { key: crypto.randomUUID() } },
      })

      channel
        .on('presence', { event: 'sync' }, () => {
          setCount(Object.keys(channel.presenceState()).length + BASE_OFFSET)
        })
        .subscribe(async (status) => {
          if (status === 'SUBSCRIBED') {
            await channel.track({ online_at: new Date().toISOString() })
          }
        })

      cleanup = () => supabase.removeChannel(channel)
    })

    return () => cleanup()
  }, [])

  return count
}

// Fixed point in time the "total views" counter starts ticking up from.
const LAUNCH_TS = new Date('2026-08-28T00:00:00Z').getTime()
const LAUNCH_VIEWS = 1240

/** Fake-but-plausible total view count that ticks up slowly over time. */
export function useTotalViews() {
  const [views, setViews] = useState(() => LAUNCH_VIEWS + Math.floor((Date.now() - LAUNCH_TS) / 45_000))

  useEffect(() => {
    const interval = setInterval(() => {
      setViews(LAUNCH_VIEWS + Math.floor((Date.now() - LAUNCH_TS) / 45_000))
    }, 30_000)
    return () => clearInterval(interval)
  }, [])

  return views
}
