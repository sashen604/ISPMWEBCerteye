import { useState, useEffect } from 'react'
import api from '../api'
import '../styles/dashboard.css'

function DashboardPage() {
  const [stats, setStats] = useState({
    total: 0,
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    expiring: 0
  })
  const [domain, setDomain] = useState('')
  const [scanning, setScanning] = useState(false)
  const [scanResult, setScanResult] = useState(null)
  const [scanError, setScanError] = useState('')
  const [certificates, setCertificates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Load statistics and certificates
  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError('')
      console.log('[Dashboard] Fetching certificates...')
      const response = await api.get('/api/certificates/')
      
      const certs = response.data.results || response.data || []
      setCertificates(certs.slice(0, 5)) // Show 5 latest

      // Calculate stats
      const statsData = {
        total: certs.length,
        critical: certs.filter(c => c.risk_level === 'critical').length,
        high: certs.filter(c => c.risk_level === 'high').length,
        medium: certs.filter(c => c.risk_level === 'medium').length,
        low: certs.filter(c => c.risk_level === 'low').length,
        expiring: certs.filter(c => c.days_remaining <= 30).length
      }
      setStats(statsData)
      console.log('[Dashboard] Dashboard data loaded successfully')
    } catch (err) {
      console.error('[Dashboard] Failed to load dashboard:', err)
      setError(err.response?.data?.detail || err.message || 'Failed to load dashboard. Please ensure you are logged in.')
    } finally {
      setLoading(false)
    }
  }

  const handleScan = async (e) => {
    e.preventDefault()
    if (!domain.trim()) return

    setScanError('')
    setScanResult(null)
    setScanning(true)

    try {
      console.log(`[Dashboard] Scanning domain: ${domain}`)
      const response = await api.post('/api/certificates/scan/', { domain })
      setScanResult(response.data)
      setDomain('')
      // Refresh stats after scan
      setTimeout(loadDashboardData, 1000)
    } catch (err) {
      console.error('[Dashboard] Failed to scan domain:', err)
      setScanError(err.response?.data?.detail || err.response?.data?.error || 'Failed to scan domain')
    } finally {
      setScanning(false)
    }
  }

  const getRiskColor = (level) => {
    const colors = {
      'critical': '#c77dff',
      'high': '#b078e0',
      'medium': '#8127ca',
      'low': '#7a21d4'
    }
    return colors[level] || '#7a21d4'
  }

  const getRiskEmoji = (level) => {
    const emojis = {
      'critical': '🔴',
      'high': '🟠',
      'medium': '🟡',
      'low': '🟢'
    }
    return emojis[level] || '⚪'
  }

  return (
    <div className="dashboard-container">
      {/* Header */}
      <div className="dashboard-header">
        <div>
          <h2 className="dashboard-title">📊 Certificate Dashboard</h2>
          <p className="dashboard-subtitle">Overview of certificate health and risk assessment</p>
        </div>
        <button className="btn btn-refresh" onClick={loadDashboardData} disabled={loading}>
          🔄 Refresh
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="alert alert-danger alert-custom">
          ⚠️ {error}
        </div>
      )}

      {/* Loading State */}
      {loading && !error && (
        <div className="alert alert-info alert-custom">
          ⏳ Loading dashboard data...
        </div>
      )}

      {/* Domain Scanner Card */}
      <div className="card dashboard-card scanner-card">
        <div className="card-header-custom">
          <h5 className="card-title-custom">🔍 Scan Public Domain</h5>
          <p className="card-subtitle">Enter a domain to retrieve its SSL/TLS certificate</p>
        </div>
        <div className="card-body-custom">
          <form onSubmit={handleScan} className="scan-form">
            <div className="input-group scan-input">
              <input
                type="text"
                className="form-control"
                placeholder="e.g., google.com, github.com, example.org"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                disabled={scanning}
              />
              <button 
                type="submit" 
                className="btn btn-scan"
                disabled={scanning || !domain.trim()}
              >
                {scanning ? '⏳ Scanning...' : '🔎 Scan'}
              </button>
            </div>
          </form>

          {scanError && (
            <div className="alert alert-danger alert-custom mt-3">
              ❌ {scanError}
            </div>
          )}

          {scanResult && (
            <div className="scan-result mt-3">
              <div className="result-header">
                <h6 className="result-domain">{scanResult.domain}</h6>
                <span className={`badge badge-risk badge-${scanResult.risk_level}`}>
                  {getRiskEmoji(scanResult.risk_level)} {scanResult.risk_level?.toUpperCase()}
                </span>
              </div>
              <div className="result-grid">
                <div className="result-item">
                  <span className="result-label">Risk Score</span>
                  <span className="result-value">{scanResult.risk_score}/100</span>
                </div>
                <div className="result-item">
                  <span className="result-label">Valid From</span>
                  <span className="result-value">{new Date(scanResult.valid_from).toLocaleDateString()}</span>
                </div>
                <div className="result-item">
                  <span className="result-label">Expires</span>
                  <span className="result-value">{new Date(scanResult.valid_to).toLocaleDateString()}</span>
                </div>
                <div className="result-item">
                  <span className="result-label">Days Left</span>
                  <span className="result-value">{scanResult.days_remaining}</span>
                </div>
              </div>
              <div className="result-details">
                <p><strong>Subject:</strong> {scanResult.subject}</p>
                <p><strong>Issuer:</strong> {scanResult.issuer}</p>
                <p><strong>Algorithm:</strong> {scanResult.signature_algorithm}</p>
                <p><strong>Key Length:</strong> {scanResult.key_length} bits</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📋</div>
          <div className="stat-content">
            <div className="stat-label">Total Certificates</div>
            <div className="stat-value">{stats.total}</div>
          </div>
        </div>

        <div className="stat-card critical">
          <div className="stat-icon">🔴</div>
          <div className="stat-content">
            <div className="stat-label">Critical</div>
            <div className="stat-value">{stats.critical}</div>
          </div>
        </div>

        <div className="stat-card high">
          <div className="stat-icon">🟠</div>
          <div className="stat-content">
            <div className="stat-label">High Risk</div>
            <div className="stat-value">{stats.high}</div>
          </div>
        </div>

        <div className="stat-card medium">
          <div className="stat-icon">🟡</div>
          <div className="stat-content">
            <div className="stat-label">Medium Risk</div>
            <div className="stat-value">{stats.medium}</div>
          </div>
        </div>

        <div className="stat-card low">
          <div className="stat-icon">🟢</div>
          <div className="stat-content">
            <div className="stat-label">Low Risk</div>
            <div className="stat-value">{stats.low}</div>
          </div>
        </div>

        <div className="stat-card expiring">
          <div className="stat-icon">⏰</div>
          <div className="stat-content">
            <div className="stat-label">Expiring Soon</div>
            <div className="stat-value">{stats.expiring}</div>
          </div>
        </div>
      </div>

      {/* Recent Certificates */}
      <div className="card dashboard-card">
        <div className="card-header-custom">
          <h5 className="card-title-custom">📜 Recent Certificates</h5>
        </div>
        <div className="table-responsive">
          <table className="table table-hover mb-0">
            <thead>
              <tr className="table-header">
                <th>Domain</th>
                <th>Risk Level</th>
                <th>Score</th>
                <th>Expires</th>
                <th>Days Left</th>
              </tr>
            </thead>
            <tbody>
              {certificates.length > 0 ? (
                certificates.map((cert) => (
                  <tr key={cert.id} className="table-row">
                    <td className="cert-domain">{cert.domain}</td>
                    <td>
                      <span className={`badge badge-risk badge-${cert.risk_level}`}>
                        {getRiskEmoji(cert.risk_level)} {cert.risk_level?.toUpperCase()}
                      </span>
                    </td>
                    <td className="risk-score">{cert.risk_score}/100</td>
                    <td>{new Date(cert.valid_to).toLocaleDateString()}</td>
                    <td>
                      <span className={`days-badge ${cert.days_remaining <= 30 ? 'expiring' : ''}`}>
                        {cert.days_remaining}d
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" className="text-center text-muted py-4">
                    No certificates yet. Scan a domain to get started!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default DashboardPage
