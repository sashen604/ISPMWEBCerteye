import { useState, useEffect } from 'react'
import api from '../api'
import '../styles/admin-panel.css'

function InternalCertificateAlertHistoryPage() {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all') // all, critical, high, medium, low
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  useEffect(() => {
    loadAlerts()
  }, [filter, page])

  const loadAlerts = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/internal-certificates/alert-history/', {
        params: {
          risk_level: filter === 'all' ? undefined : filter,
          search: search || undefined,
          page: page,
        }
      })
      setAlerts(response.data.results || response.data || [])
    } catch (err) {
      console.error('Failed to load alerts:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
    loadAlerts()
  }

  const getRiskColor = (level) => {
    const colors = {
      'CRITICAL': '#c77dff',
      'HIGH': '#b078e0',
      'MEDIUM': '#8127ca',
      'LOW': '#7a21d4',
    }
    return colors[level] || '#7a21d4'
  }

  const getRiskEmoji = (level) => {
    const emojis = {
      'CRITICAL': '🔴',
      'HIGH': '🟠',
      'MEDIUM': '🟡',
      'LOW': '🟢',
    }
    return emojis[level] || '⚪'
  }

  const getAlertType = (type) => {
    const types = {
      'expiration': '⏰ Certificate Expiring',
      'expired': '❌ Certificate Expired',
      'risk_high': '🔴 High Risk Detected',
      'risk_medium': '🟡 Medium Risk Detected',
    }
    return types[type] || type
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  if (loading && alerts.length === 0) {
    return (
      <div className="text-center p-5">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="container-fluid">
      {/* Header */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2 className="mb-1">📜 Alert History</h2>
          <p className="text-muted mb-0">View all internal certificate alerts</p>
        </div>
      </div>

      {/* Filters */}
      <div className="card card-stat p-3 mb-4">
        <div className="row g-3 align-items-end">
          <div className="col-md-4">
            <form onSubmit={handleSearch} className="input-group">
              <input 
                type="text"
                className="form-control"
                placeholder="Search hostname or domain..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              <button className="btn btn-outline-primary" type="submit">🔍 Search</button>
            </form>
          </div>

          <div className="col-md-4">
            <select 
              className="form-select"
              value={filter}
              onChange={(e) => {
                setFilter(e.target.value)
                setPage(1)
              }}
            >
              <option value="all">All Risk Levels</option>
              <option value="CRITICAL">🔴 CRITICAL</option>
              <option value="HIGH">🟠 HIGH</option>
              <option value="MEDIUM">🟡 MEDIUM</option>
              <option value="LOW">🟢 LOW</option>
            </select>
          </div>

          <div className="col-md-4">
            <button 
              className="btn btn-outline-secondary w-100"
              onClick={() => {
                setSearch('')
                setFilter('all')
                setPage(1)
              }}
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Alerts Table */}
      <div className="card card-stat">
        <div className="table-responsive">
          <table className="table table-hover mb-0">
            <thead>
              <tr>
                <th style={{ width: '15%' }}>Alert Type</th>
                <th style={{ width: '15%' }}>Hostname</th>
                <th style={{ width: '20%' }}>Domain</th>
                <th style={{ width: '12%' }}>Risk Level</th>
                <th style={{ width: '18%' }}>Triggered</th>
                <th style={{ width: '20%' }}>Details</th>
              </tr>
            </thead>
            <tbody>
              {alerts.length === 0 ? (
                <tr>
                  <td colSpan="6" className="text-center py-4 text-muted">
                    No alerts found
                  </td>
                </tr>
              ) : (
                alerts.map((alert, idx) => (
                  <tr key={idx}>
                    <td>
                      <span className="badge bg-light text-dark">
                        {getAlertType(alert.alert_type)}
                      </span>
                    </td>
                    <td>
                      <code className="text-muted">{alert.hostname || 'N/A'}</code>
                    </td>
                    <td>
                      <small>{alert.domain || 'N/A'}</small>
                    </td>
                    <td>
                      <span 
                        className="badge"
                        style={{ backgroundColor: getRiskColor(alert.risk_level) }}
                      >
                        {getRiskEmoji(alert.risk_level)} {alert.risk_level}
                      </span>
                    </td>
                    <td>
                      <small className="text-muted">{formatDate(alert.created_at)}</small>
                    </td>
                    <td>
                      <small>
                        {alert.message || 'Certificate alert'}
                      </small>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination would go here if needed */}
    </div>
  )
}

export default InternalCertificateAlertHistoryPage
