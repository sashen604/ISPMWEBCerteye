import React, { useState, useEffect } from 'react'
import { alertApi } from '../api'

function AlertsPage() {
  const [alerts, setAlerts] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })
  const [severityFilter, setSeverityFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  // Load alerts and stats
  const loadData = async () => {
    setLoading(true)
    try {
      // Build filters
      const filters = {}
      if (severityFilter) filters.severity = severityFilter
      if (typeFilter) filters.alert_type = typeFilter
      if (statusFilter === 'acknowledged') {
        filters.is_acknowledged = 'true'
      } else if (statusFilter === 'pending') {
        filters.is_acknowledged = 'false'
      }

      const [alertsRes, statsRes] = await Promise.all([
        alertApi.getAlerts(filters),
        alertApi.getAlertStats()
      ])

      setAlerts(alertsRes.results || alertsRes || [])
      setStats(statsRes)
      setMessage({ type: '', text: '' })
    } catch (err) {
      console.error('Failed to load alerts:', err)
      setMessage({ type: 'error', text: err.error || 'Failed to load alerts' })
    } finally {
      setLoading(false)
    }
  }

  // Initial load
  useEffect(() => {
    loadData()
  }, [])

  // Reload when filters change
  useEffect(() => {
    loadData()
  }, [severityFilter, typeFilter, statusFilter])

  // Auto-dismiss messages
  useEffect(() => {
    if (message.text) {
      const timer = setTimeout(() => setMessage({ type: '', text: '' }), 4000)
      return () => clearTimeout(timer)
    }
  }, [message])

  const getSeverityBadge = (severity) => {
    const badges = {
      CRITICAL: { bg: 'danger', icon: '🔴' },
      HIGH: { bg: 'warning', icon: '🟠' },
      MEDIUM: { bg: 'info', icon: '🟡' },
      LOW: { bg: 'success', icon: '🟢' }
    }
    const badge = badges[severity] || { bg: 'secondary', icon: '⚪' }
    return badge
  }

  const getAlertTypeIcon = (type) => {
    const icons = {
      EXPIRY: '⏰',
      CRYPTO_WEAKNESS: '🔐',
      OTHER: '📌'
    }
    return icons[type] || '📌'
  }

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getDaysAgo = (dateStr) => {
    const days = Math.floor((new Date() - new Date(dateStr)) / (1000 * 60 * 60 * 24))
    if (days === 0) return 'Today'
    if (days === 1) return 'Yesterday'
    return `${days} days ago`
  }

  const handleAcknowledgeAll = async () => {
    // This would require an acknowledge endpoint on the backend
    // For now, show a message that this feature requires backend support
    setMessage({
      type: 'info',
      text: 'Acknowledge All feature requires backend implementation. Individual alert acknowledgment can be added via API enhancement.'
    })
  }

  const handleRefresh = () => {
    loadData()
  }

  return (
    <div>
      {/* Header */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h3 className="mb-1">🚨 Alert Management</h3>
          <p className="text-muted">Review and manage certificate security alerts</p>
        </div>
        <div className="d-flex gap-2">
          <button
            className="btn btn-outline-secondary"
            onClick={handleRefresh}
            disabled={loading}
          >
            🔄 Refresh
          </button>
          <button
            className="btn btn-outline-danger"
            onClick={handleAcknowledgeAll}
            disabled={loading || alerts.length === 0}
          >
            ✓ Acknowledge All
          </button>
        </div>
      </div>

      {/* Status Message */}
      {message.text && (
        <div className={`alert alert-${message.type === 'success' ? 'success' : message.type === 'error' ? 'danger' : 'info'} alert-dismissible fade show`} role="alert">
          {message.text}
          <button type="button" className="btn-close" onClick={() => setMessage({ type: '', text: '' })}></button>
        </div>
      )}

      {/* Statistics Cards */}
      {stats && (
        <div className="row mb-4">
          <div className="col-md-3">
            <div className="card border-danger">
              <div className="card-body">
                <h6 className="card-title text-muted">🔴 Critical</h6>
                <h3 className="mb-0 text-danger">{stats.CRITICAL || 0}</h3>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="card border-warning">
              <div className="card-body">
                <h6 className="card-title text-muted">🟠 High</h6>
                <h3 className="mb-0 text-warning">{stats.HIGH || 0}</h3>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="card border-info">
              <div className="card-body">
                <h6 className="card-title text-muted">🟡 Medium</h6>
                <h3 className="mb-0 text-info">{stats.MEDIUM || 0}</h3>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="card border-success">
              <div className="card-body">
                <h6 className="card-title text-muted">🟢 Low</h6>
                <h3 className="mb-0 text-success">{stats.LOW || 0}</h3>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="card mb-4">
        <div className="card-header bg-light">
          <h5 className="mb-0">🔍 Filters</h5>
        </div>
        <div className="card-body">
          <div className="row">
            <div className="col-md-4">
              <label className="form-label fw-bold">Severity</label>
              <select
                className="form-select"
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
              >
                <option value="">All Severities</option>
                <option value="CRITICAL">🔴 Critical</option>
                <option value="HIGH">🟠 High</option>
                <option value="MEDIUM">🟡 Medium</option>
                <option value="LOW">🟢 Low</option>
              </select>
            </div>
            <div className="col-md-4">
              <label className="form-label fw-bold">Alert Type</label>
              <select
                className="form-select"
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
              >
                <option value="">All Types</option>
                <option value="EXPIRY">⏰ Certificate Expiry</option>
                <option value="CRYPTO_WEAKNESS">🔐 Crypto Weakness</option>
                <option value="OTHER">📌 Other</option>
              </select>
            </div>
            <div className="col-md-4">
              <label className="form-label fw-bold">Status</label>
              <select
                className="form-select"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">All Alerts</option>
                <option value="pending">⏳ Pending</option>
                <option value="acknowledged">✓ Acknowledged</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="card">
        <div className="card-header bg-light d-flex justify-content-between align-items-center">
          <h5 className="mb-0">
            {loading ? '⏳ Loading...' : `📋 Alerts (${alerts.length})`}
          </h5>
        </div>
        <div className="card-body p-0">
          {loading ? (
            <div className="p-4 text-center">
              <div className="spinner-border text-primary" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
            </div>
          ) : alerts.length === 0 ? (
            <div className="p-4 text-center text-muted">
              <p className="mb-0">✨ No alerts to display</p>
              <small>All certificates are in good standing</small>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover mb-0">
                <thead className="bg-light">
                  <tr>
                    <th style={{ width: '40%' }}>Certificate Domain</th>
                    <th style={{ width: '15%' }}>Type</th>
                    <th style={{ width: '15%' }}>Severity</th>
                    <th style={{ width: '15%' }}>Created</th>
                    <th style={{ width: '15%' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {alerts.map((alert) => {
                    const severityBadge = getSeverityBadge(alert.severity)
                    return (
                      <tr key={alert.id} className={alert.is_acknowledged ? 'opacity-50' : ''}>
                        <td>
                          <div>
                            <strong>{alert.certificate_domain || alert.message}</strong>
                            <br />
                            <small className="text-muted">{alert.message}</small>
                          </div>
                        </td>
                        <td>
                          <span className="me-2">{getAlertTypeIcon(alert.alert_type)}</span>
                          {alert.alert_type === 'EXPIRY' && 'Certificate Expiry'}
                          {alert.alert_type === 'CRYPTO_WEAKNESS' && 'Crypto Weakness'}
                          {alert.alert_type === 'OTHER' && 'Other'}
                        </td>
                        <td>
                          <span className={`badge bg-${severityBadge.bg}`}>
                            {severityBadge.icon} {alert.severity}
                          </span>
                        </td>
                        <td>
                          <small>
                            {formatDate(alert.created_at)}
                            <br />
                            <span className="text-muted">{getDaysAgo(alert.created_at)}</span>
                          </small>
                        </td>
                        <td>
                          {alert.is_acknowledged ? (
                            <span className="badge bg-success">✓ Acknowledged</span>
                          ) : (
                            <span className="badge bg-warning text-dark">⏳ Pending</span>
                          )}
                          {alert.acknowledged_by && (
                            <br />
                          )}
                          {alert.acknowledged_by && (
                            <small className="text-muted">by {alert.acknowledged_by}</small>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Info Section */}
      <div className="row mt-4">
        <div className="col-md-12">
          <div className="alert alert-info alert-sm">
            <small>
              <strong>💡 Alert Types:</strong> Certificate Expiry alerts warn about upcoming expirations, while Crypto Weakness alerts identify cryptographic issues like weak keys, algorithms, or self-signed certificates.
              <br />
              <strong>🔔 Auto-Generated:</strong> Alerts are automatically generated based on certificate analysis. Critical alerts require immediate action.
            </small>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AlertsPage
