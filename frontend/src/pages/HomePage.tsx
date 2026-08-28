import { useSpots } from '../hooks/useSpots'
import SpotsGrid from '../components/SpotsGrid'
import Thermometer from '../components/Thermometer'

export default function HomePage() {
  const { spots, total, loading } = useSpots()

  if (loading) return <div className="p-8 text-center">Cargando...</div>

  return (
    <div className="min-h-screen bg-bg text-ink">
      <header className="border-b border-border sticky top-0 z-20 bg-bg/95 backdrop-blur">
        <div className="max-w-5xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="text-2xl font-bold">Marcá Mi Notebook</div>
          <a href="/admin" className="text-celeste text-sm">Admin</a>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold mb-4">Tu marca, en mi notebook.</h1>
        <p className="text-lg text-ink-soft mb-6">10 lugares de sticker. Gana el que más ofrece.</p>

        <SpotsGrid spots={spots} onRefresh={() => {}} />
        <Thermometer raised={total} />

        <section className="mt-12">
          <h2 className="text-2xl font-bold mb-6">FAQ</h2>
          <div className="space-y-4">
            <div className="bg-surface p-4 rounded-lg border border-border">
              <h3 className="font-bold mb-2">¿Esto es en serio?</h3>
              <p className="text-ink-soft text-sm">Sí. Las pujas son reales y el sticker se pega de verdad.</p>
            </div>
            <div className="bg-surface p-4 rounded-lg border border-border">
              <h3 className="font-bold mb-2">¿Me devolveís el dinero si me superan?</h3>
              <p className="text-ink-soft text-sm">Sí. Si alguien puja más alto, te devolvemos automáticamente.</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
