import { useSpots } from '../hooks/useSpots'
import { useLiveVisitors, useTotalViews } from '../hooks/useLiveVisitors'
import SpotsGrid from '../components/SpotsGrid'
import Thermometer from '../components/Thermometer'
import Countdown from '../components/Countdown'
import CurrencyToggle from '../components/CurrencyToggle'
import HowItWorks from '../components/HowItWorks'
import TheMachine from '../components/TheMachine'
import LiveAuctionTable from '../components/LiveAuctionTable'
import AboutMe from '../components/AboutMe'
import { Link } from 'react-router-dom'

export default function HomePage({ auctionEndsAt }: { auctionEndsAt: string | null }) {
  const { spots, total, loading } = useSpots()
  const visitors = useLiveVisitors()
  const totalViews = useTotalViews()

  if (loading) return <div className="p-8 text-center">Cargando...</div>

  return (
    <div className="min-h-screen bg-bg text-ink">
      <header className="border-b border-border sticky top-0 z-20 bg-bg/95 backdrop-blur">
        <div className="max-w-5xl mx-auto px-4 py-4 flex justify-between items-center gap-4">
          <div className="text-2xl font-bold">Marcá Mi Notebook</div>
          <nav className="hidden sm:flex items-center gap-6 text-sm text-ink-soft">
            <a href="#subasta" className="hover:text-ink">Subasta en vivo</a>
            <a href="#como-funciona" className="hover:text-ink">Cómo funciona</a>
            <a href="#la-maquina" className="hover:text-ink">La máquina</a>
            <a href="#faq" className="hover:text-ink">FAQ</a>
          </nav>
          <div className="flex items-center gap-3">
            <CurrencyToggle />
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        <p className="text-xs text-ink-faint mb-3 flex items-center gap-1.5">
          <span className="inline-block w-2 h-2 rounded-full bg-live" />
          {visitors} {visitors === 1 ? 'persona viendo esto ahora' : 'personas viendo esto ahora'}
          <span className="text-border">·</span>
          {totalViews.toLocaleString('es-AR')} vistas en total
        </p>

        <h1 className="text-4xl font-bold mb-4">Tu marca, en mi notebook.</h1>
        <p className="text-lg text-ink-soft mb-2">10 lugares de sticker. Gana el que más ofrece.</p>
        {auctionEndsAt && (
          <p className="text-sm text-ink-soft mb-6">
            <Countdown endsAt={auctionEndsAt} /> · todavía podés superar cualquier oferta
          </p>
        )}

        <SpotsGrid spots={spots} onRefresh={() => {}} />
        <Thermometer raised={total} />

        <div id="subasta">
          <LiveAuctionTable spots={spots} />
        </div>
        <div id="como-funciona">
          <HowItWorks />
        </div>
        <div id="la-maquina">
          <TheMachine />
        </div>
        <AboutMe />

        <section id="faq" className="mt-12">
          <h2 className="text-2xl font-bold mb-6">FAQ</h2>
          <div className="space-y-4">
            <div className="bg-surface p-4 rounded-lg border border-border">
              <h3 className="font-bold mb-2">¿Esto es en serio?</h3>
              <p className="text-ink-soft text-sm">Sí. Las pujas son reales y el sticker se pega de verdad.</p>
            </div>
            <div className="bg-surface p-4 rounded-lg border border-border">
              <h3 className="font-bold mb-2">¿Me devolvés el dinero si me superan?</h3>
              <p className="text-ink-soft text-sm">Sí. Si alguien puja más alto, te devolvemos automáticamente.</p>
            </div>
            <div className="bg-surface p-4 rounded-lg border border-border">
              <h3 className="font-bold mb-2">¿Qué obtengo exactamente?</h3>
              <p className="text-ink-soft text-sm">
                Un sticker de vinilo troquelado con tu logo, pegado en la notebook, más un lugar en esta página con
                link a tu sitio. No te prometo métricas, sí que la notebook anda conmigo a todos lados.
              </p>
            </div>
            <div className="bg-surface p-4 rounded-lg border border-border">
              <h3 className="font-bold mb-2">¿Cómo funciona el pago?</h3>
              <p className="text-ink-soft text-sm">
                Pagás el total de tu oferta al momento de pujar, con Mercado Pago. Si te superan, se devuelve
                automáticamente.
              </p>
            </div>
            <div className="bg-surface p-4 rounded-lg border border-border">
              <h3 className="font-bold mb-2">¿Puede sumarse cualquier marca?</h3>
              <p className="text-ink-soft text-sm">
                Casi. Reviso cada logo antes de que aparezca — al final viaja conmigo. Si rechazo tu oferta, te
                devuelvo el pago completo.
              </p>
            </div>
            <div className="bg-surface p-4 rounded-lg border border-border">
              <h3 className="font-bold mb-2">¿Por qué no comprás la notebook directo?</h3>
              <p className="text-ink-soft text-sm">
                La necesito hoy y esto la financia más rápido — y de paso le da visibilidad real a las marcas que
                se suman.
              </p>
            </div>
            <div className="bg-surface p-4 rounded-lg border border-border">
              <h3 className="font-bold mb-2">¿Qué pasa cuando termina la subasta?</h3>
              <p className="text-ink-soft text-sm">
                Los lugares se cierran con la oferta más alta de cada uno. Imprimo y pego los stickers en los días
                siguientes.
              </p>
            </div>
          </div>
        </section>

        <footer className="mt-16 pt-6 border-t border-border text-xs text-ink-faint flex flex-wrap gap-x-4 gap-y-2 justify-between">
          <span>Marcá Mi Notebook no está afiliado, respaldado ni patrocinado por Apple Inc.</span>
          <span className="flex gap-4">
            <Link to="/privacy" className="hover:text-ink-soft">Privacidad</Link>
            <Link to="/terms" className="hover:text-ink-soft">Términos</Link>
          </span>
        </footer>
      </main>
    </div>
  )
}
