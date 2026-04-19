import { Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import AdminLayout from './layouts/AdminLayout.jsx'
import LoginPage from './pages/LoginPage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import CertificatesPage from './pages/CertificatesPage.jsx'
import AlertsPage from './pages/AlertsPage.jsx'
import InternalCertificatesPage from './pages/InternalCertificatesPage.jsx'
import SettingsPage from './pages/SettingsPage.jsx'
import { isAuthenticated } from './services/auth'

// Protected route component
function ProtectedRoute({ children }) {
  const [authState, setAuthState] = useState(null)

  useEffect(() => {
    setAuthState(isAuthenticated())
  }, [])

  if (authState === null) {
    return <div className="d-flex justify-content-center align-items-center" style={{ height: '100vh' }}>Loading...</div>
  }

  return authState ? children : <Navigate to="/login" replace />
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route 
        path="/" 
        element={
          <ProtectedRoute>
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="certificates" element={<CertificatesPage />} />
        <Route path="alerts" element={<AlertsPage />} />
        <Route path="internal-certificates" element={<InternalCertificatesPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default App