import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import HomePage from './pages/HomePage'
import AdminPage from './pages/AdminPage'

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
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/admin" element={<AdminPage />} />
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
  )
}

export default App
