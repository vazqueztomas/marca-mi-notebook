import { useState } from 'react'
import AdminLogin from '../components/AdminLogin'
import AdminSpots from '../components/AdminSpots'

export default function AdminPage() {
  const [token, setToken] = useState<string | null>(
    typeof window !== 'undefined' ? localStorage.getItem('admin_token') : null
  )

  const handleLogin = (newToken: string) => {
    localStorage.setItem('admin_token', newToken)
    setToken(newToken)
  }

  const handleLogout = () => {
    localStorage.removeItem('admin_token')
    setToken(null)
  }

  if (!token) {
    return <AdminLogin onLogin={handleLogin} />
  }

  return (
    <div className="min-h-screen bg-bg text-ink">
      <header className="border-b border-border">
        <div className="max-w-5xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold">Admin Panel</h1>
          <button
            onClick={handleLogout}
            className="text-sm text-celeste hover:underline"
          >
            Logout
          </button>
        </div>
      </header>
      <AdminSpots />
    </div>
  )
}
