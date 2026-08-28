import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import HomePage from './pages/HomePage'
import AdminPage from './pages/AdminPage'
import LegalPage from './pages/LegalPage'
import { CurrencyProvider } from './context/CurrencyContext'
import { useMeta } from './hooks/useMeta'

function PaymentResult({ message }: { message: string }) {
  return (
    <div className="min-h-screen bg-bg text-ink flex flex-col items-center justify-center gap-4 px-4 text-center">
      <p className="text-xl font-semibold">{message}</p>
      <Link to="/" className="text-celeste hover:underline">
        Volver al inicio
      </Link>
    </div>
  )
}

function App() {
  const { auctionEndsAt, arsPerUsd } = useMeta()

  return (
    <CurrencyProvider arsPerUsd={arsPerUsd}>
      <Router>
        <Routes>
          <Route path="/" element={<HomePage auctionEndsAt={auctionEndsAt} />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/privacy" element={<LegalPage page="privacy" />} />
          <Route path="/terms" element={<LegalPage page="terms" />} />
          <Route
            path="/success"
            element={<PaymentResult message="¡Pago aprobado! Gracias por tu oferta." />}
          />
          <Route
            path="/failure"
            element={<PaymentResult message="El pago fue rechazado. Probá de nuevo." />}
          />
          <Route
            path="/pending"
            element={<PaymentResult message="Tu pago está pendiente. Te avisamos cuando se acredite." />}
          />
        </Routes>
      </Router>
    </CurrencyProvider>
  )
}

export default App
