import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { logout } from '../services/auth'
import api from '../api'

function AdminLayout() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchProfile()
  }, [])

  const fetchProfile = async () => {
    try {
      const response = await api.get('/api/auth/profile')
      setUser(response.data.user)
    } catch (err) {
      console.error('Failed to fetch profile:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    try {
      await logout()
    } catch (error) {
      // ignore logout errors
    }
    navigate('/login')
  }

  return (
    <div className="d-flex">
      <aside className="sidebar p-3">
        <div className="mb-4">
          <h4 className="fw-bold">🔐 CertEye</h4>
          <small className="text-muted">
            {loading ? 'Loading...' : user?.role_display || 'Console'}
          </small>
        </div>
        <nav className="nav flex-column gap-1">
          <NavLink className="nav-link" to="/dashboard">📊 Dashboard</NavLink>
          <NavLink className="nav-link" to="/dashboard/certificates">🔒 Certificates</NavLink>
          <NavLink className="nav-link" to="/dashboard/internal-certificates">🏢 Internal Certs</NavLink>
          <NavLink className="nav-link" to="/dashboard/alerts">⚠️ Alerts</NavLink>
          <NavLink className="nav-link" to="/dashboard/internal-alerts">🔔 Internal Alerts</NavLink>
          <NavLink className="nav-link" to="/dashboard/internal-alerts-history">📜 Alert History</NavLink>
          {user?.is_superadmin && (
            <>
              <NavLink className="nav-link admin-link" to="/admin/panel">👨‍💼 Admin Panel</NavLink>
              <NavLink className="nav-link admin-link" to="/admin/users">👥 User Management</NavLink>
              <NavLink className="nav-link admin-link" to="/admin/adcs">🏢 AD CS Management</NavLink>
            </>
          )}
          <NavLink className="nav-link" to="/dashboard/settings">⚙️ Settings</NavLink>
        </nav>
      </aside>
      <div className="flex-grow-1">
        <header className="topbar px-4 py-3 d-flex justify-content-between align-items-center">
          <div>
            <h5 className="mb-0">SSL Certificate Lifecycle Management</h5>
            <small className="text-muted">
              {user ? `${user.username} (${user.role_display})` : 'Monitor and secure certificate health'}
            </small>
          </div>
          <button className="btn btn-outline-primary btn-sm" onClick={handleLogout}>Logout</button>
        </header>
        <main className="content-area">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default AdminLayout