import { Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import AdminLayout from './layouts/AdminLayout.jsx'
import HomePage from './pages/HomePage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import AdminPanelPage from './pages/AdminPanelPage.jsx'
import CertificatesPage from './pages/CertificatesPage.jsx'
import AlertsPage from './pages/AlertsPage.jsx'
import InternalCertificatesPage from './pages/InternalCertificatesPage.jsx'
import InternalCertificateAlertsPage from './pages/InternalCertificateAlertsPage.jsx'
import InternalCertificateAlertHistoryPage from './pages/InternalCertificateAlertHistoryPage.jsx'
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
      {/* Public routes */}
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      
      {/* Protected routes */}
      <Route 
        path="/dashboard" 
        element={
          <ProtectedRoute>
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="certificates" element={<CertificatesPage />} />
        <Route path="alerts" element={<AlertsPage />} />
        <Route path="internal-certificates" element={<InternalCertificatesPage />} />
        <Route path="internal-alerts" element={<InternalCertificateAlertsPage />} />
        <Route path="internal-alerts-history" element={<InternalCertificateAlertHistoryPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>

      {/* Protected admin layout with nested routes */}
      <Route 
        path="/admin" 
        element={
          <ProtectedRoute>
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/admin/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="panel" element={<AdminPanelPage />} />
        <Route path="certificates" element={<CertificatesPage />} />
        <Route path="alerts" element={<AlertsPage />} />
        <Route path="internal-certificates" element={<InternalCertificatesPage />} />
        <Route path="internal-alerts" element={<InternalCertificateAlertsPage />} />
        <Route path="internal-alerts-history" element={<InternalCertificateAlertHistoryPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App