import { useEffect } from 'react'
import { Link } from 'react-router-dom'

function Privacy() {
  return (
    <>
      <h1 className="text-2xl font-bold mb-4">Privacidad</h1>
      <p>
        Guardamos tu nombre, email y logo únicamente para gestionar tu oferta: mostrar el sticker en el lugar que
        ganaste y contactarte si hace falta. No vendemos ni compartimos tus datos con terceros, más allá de
        Mercado Pago para procesar el cobro.
      </p>
      <p>Podés pedirnos que borremos tus datos escribiéndonos por los medios de contacto de este sitio.</p>
    </>
  )
}

function Terms() {
  return (
    <>
      <h1 className="text-2xl font-bold mb-4">Términos</h1>
      <p>
        Cada oferta paga se cobra al momento. Si alguien te supera, te devolvemos el dinero automáticamente. Nos
        reservamos el derecho de rechazar cualquier marca antes de pegar el sticker; si rechazamos tu oferta, te
        devolvemos el pago completo.
      </p>
      <p>El sticker se pega en un plazo razonable luego de cerrada la subasta de cada lugar.</p>
      <p className="text-ink-faint text-xs">
        Marcá Mi Notebook no está afiliado, respaldado ni patrocinado por Apple Inc. MacBook y Mac son marcas
        registradas de Apple Inc.
      </p>
    </>
  )
}

export default function LegalPage({ page }: { page: 'privacy' | 'terms' }) {
  useEffect(() => {
    document.title = page === 'privacy'
      ? 'Privacidad — Marcá Mi Notebook'
      : 'Términos — Marcá Mi Notebook'
    return () => { document.title = 'Marcá Mi Notebook' }
  }, [page])

  return (
    <div className="min-h-screen bg-bg text-ink">
      <div className="max-w-2xl mx-auto px-4 py-12 space-y-4 text-sm text-ink-soft">
        {page === 'privacy' ? <Privacy /> : <Terms />}
        <Link to="/" className="inline-block text-celeste hover:underline pt-4">
          Volver al inicio
        </Link>
      </div>
    </div>
  )
}
