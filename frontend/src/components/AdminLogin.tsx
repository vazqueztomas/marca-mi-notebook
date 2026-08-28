import { useState } from 'react'
import { adminAPI } from '../api'

interface AdminLoginProps {
  onLogin: (token: string) => void
}

export default function AdminLogin({ onLogin }: AdminLoginProps) {
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    const password = (e.currentTarget.elements.namedItem('password') as HTMLInputElement).value

    try {
      const res = await adminAPI.login(password)
      onLogin(res.data.token)
    } catch (err: any) {
      setError(err.response?.status === 401 ? 'Contraseña incorrecta' : 'Error al conectar')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-md mx-auto mt-20 space-y-4">
      <h2 className="text-2xl font-bold">Panel de administración</h2>
      <input
        type="password"
        name="password"
        placeholder="Contraseña"
        required
        className="w-full px-3 py-2 border border-border rounded"
      />
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <button
        type="submit"
        disabled={loading}
        className="w-full bg-ink text-bg font-semibold py-2 rounded hover:opacity-90 disabled:opacity-50"
      >
        {loading ? 'Entrando...' : 'Entrar'}
      </button>
    </form>
  )
}
