import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { logout } from '../services/auth'

function AdminLayout() {
  const navigate = useNavigate()

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
          <h4 className="fw-bold">SSL Lifecycle</h4>
          <small className="text-muted">Admin Console</small>
        </div>
        <nav className="nav flex-column gap-1">
          <NavLink className="nav-link" to="/dashboard">Dashboard</NavLink>
          <NavLink className="nav-link" to="/certificates">Certificates</NavLink>
          <NavLink className="nav-link" to="/internal-certificates">Internal Certificates</NavLink>
          <NavLink className="nav-link" to="/alerts">Alerts</NavLink>
          <NavLink className="nav-link" to="/settings">Settings</NavLink>
        </nav>
      </aside>
      <div className="flex-grow-1">
        <header className="topbar px-4 py-3 d-flex justify-content-between align-items-center">
          <div>
            <h5 className="mb-0">SSL Certificate Lifecycle Management</h5>
            <small className="text-muted">Monitor and secure certificate health</small>
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
