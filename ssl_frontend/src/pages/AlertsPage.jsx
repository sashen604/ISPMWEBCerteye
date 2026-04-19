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
  const [searchTerm, setSearchTerm] = useState('')
  const [expandedAlertId, setExpandedAlertId] = useState(null)
  const [sortBy, setSortBy] = useState('created')
  const [sortOrder, setSortOrder] = useState('desc')

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

      // Handle different response formats
      let alertsData = []
      if (Array.isArray(alertsRes)) {
        alertsData = alertsRes
      } else if (alertsRes && Array.isArray(alertsRes.results)) {
        alertsData = alertsRes.results
      } else if (alertsRes && typeof alertsRes === 'object') {
        // If it's an object but not an array, try to extract data
        alertsData = alertsRes.data || alertsRes.alerts || []
      }

      // Handle stats response - extract severity counts
      let statsData = {}
      if (statsRes && typeof statsRes === 'object') {
        // Check if stats has by_severity breakdown
        if (statsRes.by_severity) {
          statsData = statsRes.by_severity
        } else if (statsRes.severity_breakdown) {
          statsData = statsRes.severity_breakdown
        } else if (statsRes.CRITICAL !== undefined) {
          // Direct format: {CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0}
          statsData = statsRes
        } else {
          // Try to count from alerts
          statsData = calculateStatsFromAlerts(alertsData)
        }
      } else {
        // Fallback: calculate from alerts
        statsData = calculateStatsFromAlerts(alertsData)
      }
      
      setAlerts(alertsData)
      setStats(statsData)
      setMessage({ type: '', text: '' })
      
      // Debug log
      console.log('Stats loaded:', statsData)
      console.log('Alerts loaded:', alertsData.length)
      console.log('Raw statsRes:', statsRes)
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

  // Get urgency level based on severity
  const getUrgencyLevel = (severity) => {
    const levels = {
      CRITICAL: { level: 'URGENT', color: 'danger', action: 'Action required immediately' },
      HIGH: { level: 'Important', color: 'warning', action: 'Action recommended soon' },
      MEDIUM: { level: 'Notice', color: 'info', action: 'Monitor and plan accordingly' },
      LOW: { level: 'Info', color: 'success', action: 'For reference' }
    }
    return levels[severity] || levels.LOW
  }

  // Calculate stats from alerts if needed
  const calculateStatsFromAlerts = (alertsArray) => {
    const calculated = {
      CRITICAL: 0,
      HIGH: 0,
      MEDIUM: 0,
      LOW: 0
    }
    
    if (Array.isArray(alertsArray)) {
      alertsArray.forEach(alert => {
        if (alert.severity === 'CRITICAL') calculated.CRITICAL++
        else if (alert.severity === 'HIGH') calculated.HIGH++
        else if (alert.severity === 'MEDIUM') calculated.MEDIUM++
        else if (alert.severity === 'LOW') calculated.LOW++
      })
    }
    
    return calculated
  }

  // Filter and sort alerts
  const getFilteredAndSortedAlerts = () => {
    let filtered = alerts.filter(alert => {
      // Severity filter
      if (severityFilter && alert.severity !== severityFilter) return false
      // Type filter
      if (typeFilter && alert.alert_type !== typeFilter) return false
      // Status filter
      if (statusFilter === 'acknowledged' && !alert.is_acknowledged) return false
      if (statusFilter === 'pending' && alert.is_acknowledged) return false
      // Search filter
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase()
        return (
          alert.certificate_domain?.toLowerCase().includes(searchLower) ||
          alert.message?.toLowerCase().includes(searchLower) ||
          alert.severity?.toLowerCase().includes(searchLower)
        )
      }
      return true
    })

    // Sort
    filtered.sort((a, b) => {
      let aVal, bVal
      if (sortBy === 'created') {
        aVal = new Date(a.created_at)
        bVal = new Date(b.created_at)
      } else if (sortBy === 'severity') {
        const severityOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 }
        aVal = severityOrder[a.severity] || 999
        bVal = severityOrder[b.severity] || 999
      } else if (sortBy === 'domain') {
        aVal = a.certificate_domain || ''
        bVal = b.certificate_domain || ''
      }

      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : aVal < bVal ? -1 : 0
      } else {
        return aVal < bVal ? 1 : aVal > bVal ? -1 : 0
      }
    })

    return filtered
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

  const filteredAlerts = getFilteredAndSortedAlerts()

  return (
    <div>
      {/* Header with Quick Stats */}
      <div className="mb-4">
        <div className="d-flex justify-content-between align-items-start mb-3">
          <div>
            <h2 className="mb-2">
              <span style={{ fontSize: '2rem' }}>🚨</span> Alert Management
            </h2>
            <p className="text-muted mb-0">Monitor and manage certificate security alerts in real-time</p>
          </div>
          <div className="d-flex gap-2">
            <button
              className="btn btn-outline-secondary"
              onClick={handleRefresh}
              disabled={loading}
              title="Refresh alerts"
            >
              {loading ? '⏳ Refreshing...' : '🔄 Refresh'}
            </button>
            <button
              className="btn btn-outline-danger"
              onClick={handleAcknowledgeAll}
              disabled={loading || !Array.isArray(alerts) || alerts.length === 0}
              title="Mark all alerts as acknowledged"
            >
              ✓ Acknowledge All
            </button>
          </div>
        </div>

        {/* Alert Summary Stats */}
        {stats && Object.keys(stats).length > 0 ? (
          <div className="row g-2">
            <div className="col-6 col-sm-4 col-md-3 col-lg-2">
              <div className="card border-0 shadow-sm bg-danger bg-opacity-10">
                <div className="card-body p-3 text-center">
                  <div className="text-danger" style={{ fontSize: '1.5rem' }}>🔴</div>
                  <h4 className="mb-0 text-danger fw-bold">{stats.CRITICAL ?? 0}</h4>
                  <small className="text-muted">Critical</small>
                </div>
              </div>
            </div>
            <div className="col-6 col-sm-4 col-md-3 col-lg-2">
              <div className="card border-0 shadow-sm bg-warning bg-opacity-10">
                <div className="card-body p-3 text-center">
                  <div className="text-warning" style={{ fontSize: '1.5rem' }}>🟠</div>
                  <h4 className="mb-0 text-warning fw-bold">{stats.HIGH ?? 0}</h4>
                  <small className="text-muted">High</small>
                </div>
              </div>
            </div>
            <div className="col-6 col-sm-4 col-md-3 col-lg-2">
              <div className="card border-0 shadow-sm bg-info bg-opacity-10">
                <div className="card-body p-3 text-center">
                  <div className="text-info" style={{ fontSize: '1.5rem' }}>🟡</div>
                  <h4 className="mb-0 text-info fw-bold">{stats.MEDIUM ?? 0}</h4>
                  <small className="text-muted">Medium</small>
                </div>
              </div>
            </div>
            <div className="col-6 col-sm-4 col-md-3 col-lg-2">
              <div className="card border-0 shadow-sm bg-success bg-opacity-10">
                <div className="card-body p-3 text-center">
                  <div className="text-success" style={{ fontSize: '1.5rem' }}>🟢</div>
                  <h4 className="mb-0 text-success fw-bold">{stats.LOW ?? 0}</h4>
                  <small className="text-muted">Low</small>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="row g-2">
            <div className="col-12">
              <p className="text-muted text-center">Loading statistics...</p>
            </div>
          </div>
        )}
      </div>

      {/* Status Message */}
      {message.text && (
        <div
          className={`alert alert-${message.type === 'success' ? 'success' : message.type === 'error' ? 'danger' : 'info'} alert-dismissible fade show d-flex align-items-center`}
          role="alert"
          style={{ borderRadius: '8px' }}
        >
          <span className="me-2" style={{ fontSize: '1.2rem' }}>
            {message.type === 'success' ? '✅' : message.type === 'error' ? '❌' : 'ℹ️'}
          </span>
          <div className="flex-grow-1">{message.text}</div>
          <button
            type="button"
            className="btn-close"
            onClick={() => setMessage({ type: '', text: '' })}
          ></button>
        </div>
      )}

      {/* Search and Filters */}
      <div className="card mb-4 shadow-sm">
        <div className="card-header bg-light border-bottom" style={{ borderRadius: '8px 8px 0 0' }}>
          <h5 className="mb-0">
            <span>🔍</span> Search & Filter Alerts
          </h5>
        </div>
        <div className="card-body">
          {/* Search Box */}
          <div className="mb-3">
            <input
              type="text"
              className="form-control form-control-lg"
              placeholder="🔎 Search by domain, message, or severity..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ borderRadius: '8px' }}
            />
          </div>

          {/* Filter and Sort Controls */}
          <div className="row g-3">
            <div className="col-md-3">
              <label className="form-label fw-bold small">
                <span>🎯</span> Severity
              </label>
              <select
                className="form-select"
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                style={{ borderRadius: '6px' }}
              >
                <option value="">All Severities</option>
                <option value="CRITICAL">🔴 Critical</option>
                <option value="HIGH">🟠 High</option>
                <option value="MEDIUM">🟡 Medium</option>
                <option value="LOW">🟢 Low</option>
              </select>
            </div>

            <div className="col-md-3">
              <label className="form-label fw-bold small">
                <span>📌</span> Alert Type
              </label>
              <select
                className="form-select"
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                style={{ borderRadius: '6px' }}
              >
                <option value="">All Types</option>
                <option value="EXPIRY">⏰ Certificate Expiry</option>
                <option value="CRYPTO_WEAKNESS">🔐 Crypto Weakness</option>
                <option value="OTHER">📋 Other</option>
              </select>
            </div>

            <div className="col-md-2">
              <label className="form-label fw-bold small">
                <span>⏳</span> Status
              </label>
              <select
                className="form-select"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{ borderRadius: '6px' }}
              >
                <option value="">All Alerts</option>
                <option value="pending">⏳ Pending</option>
                <option value="acknowledged">✓ Acknowledged</option>
              </select>
            </div>

            <div className="col-md-2">
              <label className="form-label fw-bold small">
                <span>↕️</span> Sort By
              </label>
              <select
                className="form-select"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                style={{ borderRadius: '6px' }}
              >
                <option value="created">Date Created</option>
                <option value="severity">Severity</option>
                <option value="domain">Domain</option>
              </select>
            </div>

            <div className="col-md-2 d-flex align-items-end">
              <button
                className={`btn btn-sm w-100 ${sortOrder === 'asc' ? 'btn-primary' : 'btn-outline-secondary'}`}
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                style={{ borderRadius: '6px' }}
                title={`Currently sorting ${sortOrder === 'asc' ? 'ascending' : 'descending'}`}
              >
                {sortOrder === 'asc' ? '⬆️ Ascending' : '⬇️ Descending'}
              </button>
            </div>
          </div>

          {/* Active Filters Summary */}
          {(severityFilter || typeFilter || statusFilter || searchTerm) && (
            <div className="mt-3">
              <small className="text-muted">
                <strong>Active filters:</strong>{' '}
                {severityFilter && `Severity: ${severityFilter}`}
                {typeFilter && `${severityFilter ? ' | ' : ''}Type: ${typeFilter}`}
                {statusFilter && `${severityFilter || typeFilter ? ' | ' : ''}Status: ${statusFilter}`}
                {searchTerm && `${severityFilter || typeFilter || statusFilter ? ' | ' : ''}Search: "${searchTerm}"`}
              </small>
              <button
                className="btn btn-link btn-sm ms-2 p-0"
                onClick={() => {
                  setSeverityFilter('')
                  setTypeFilter('')
                  setStatusFilter('')
                  setSearchTerm('')
                }}
              >
                Clear all filters
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Alerts List */}
      <div className="card shadow-sm">
        <div className="card-header bg-light d-flex justify-content-between align-items-center" style={{ borderRadius: '8px 8px 0 0' }}>
          <h5 className="mb-0">
            {loading ? '⏳ Loading alerts...' : `📋 Alerts (${filteredAlerts.length}${alerts.length !== filteredAlerts.length ? ` of ${alerts.length}` : ''})`}
          </h5>
        </div>

        <div className="card-body p-0">
          {loading ? (
            <div className="p-5 text-center">
              <div className="spinner-border text-primary mb-3" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
              <p className="text-muted">Loading alerts...</p>
            </div>
          ) : !Array.isArray(filteredAlerts) || filteredAlerts.length === 0 ? (
            <div className="p-5 text-center">
              <div style={{ fontSize: '2rem' }} className="mb-3">✨</div>
              <h6 className="text-muted mb-0">No alerts to display</h6>
              <small className="text-muted">
                {searchTerm || severityFilter || typeFilter || statusFilter
                  ? 'Try adjusting your filters'
                  : 'All certificates are in good standing'}
              </small>
            </div>
          ) : (
            <div style={{ maxHeight: 'calc(100vh - 400px)', overflowY: 'auto' }}>
              {filteredAlerts.map((alert) => {
                const severityBadge = getSeverityBadge(alert.severity)
                const urgency = getUrgencyLevel(alert.severity)
                const isExpanded = expandedAlertId === alert.id

                return (
                  <div
                    key={alert.id}
                    className={`border-bottom ${alert.is_acknowledged ? 'opacity-75' : ''}`}
                    style={{ transition: 'background-color 0.2s' }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#f8f9fa')}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'white')}
                  >
                    <div
                      className="p-3"
                      style={{ cursor: 'pointer' }}
                      onClick={() =>
                        setExpandedAlertId(isExpanded ? null : alert.id)
                      }
                    >
                      <div className="row align-items-center">
                        <div className="col-auto">
                          <div
                            style={{
                              width: '4px',
                              height: '100%',
                              backgroundColor:
                                alert.severity === 'CRITICAL'
                                  ? '#dc3545'
                                  : alert.severity === 'HIGH'
                                  ? '#ffc107'
                                  : alert.severity === 'MEDIUM'
                                  ? '#0dcaf0'
                                  : '#198754',
                              borderRadius: '2px',
                              minHeight: '50px'
                            }}
                          ></div>
                        </div>
                        <div className="col">
                          <div className="row align-items-center">
                            <div className="col-md-6">
                              <h6 className="mb-1 fw-bold">
                                {getAlertTypeIcon(alert.alert_type)}{' '}
                                {alert.certificate_domain || 'Unknown Domain'}
                              </h6>
                              <small className="text-muted d-block text-truncate">
                                {alert.message}
                              </small>
                            </div>
                            <div className="col-md-2">
                              <span className={`badge bg-${severityBadge.bg} w-100`}>
                                {severityBadge.icon} {alert.severity}
                              </span>
                            </div>
                            <div className="col-md-2">
                              {alert.is_acknowledged ? (
                                <span className="badge bg-success">✓ Acknowledged</span>
                              ) : (
                                <span className="badge bg-warning text-dark">⏳ Pending</span>
                              )}
                            </div>
                            <div className="col-md-2 text-end">
                              <small className="text-muted">
                                {getDaysAgo(alert.created_at)}
                              </small>
                              <br />
                              <span
                                className={`badge bg-${urgency.color} bg-opacity-10 text-${urgency.color}`}
                              >
                                {urgency.level}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="col-auto">
                          <span
                            className="text-muted"
                            style={{ fontSize: '1.2rem' }}
                          >
                            {isExpanded ? '▼' : '▶'}
                          </span>
                        </div>
                      </div>

                      {/* Expanded Details */}
                      {isExpanded && (
                        <div className="mt-3 pt-3 border-top">
                          <div className="row">
                            <div className="col-md-6">
                              <small>
                                <strong>📝 Full Message:</strong>
                                <br />
                                {alert.message}
                              </small>
                            </div>
                            <div className="col-md-6">
                              <small>
                                <strong>⏰ Timeline:</strong>
                                <br />
                                Created: {formatDate(alert.created_at)}
                                <br />
                                {alert.is_acknowledged &&
                                  `Acknowledged: ${alert.acknowledged_at || 'N/A'}`}
                              </small>
                            </div>
                          </div>
                          <div className="row mt-2">
                            <div className="col-md-6">
                              <small>
                                <strong>🔍 Alert Details:</strong>
                                <br />
                                Type: {alert.alert_type}
                                <br />
                                Severity: {alert.severity}
                              </small>
                            </div>
                            <div className="col-md-6">
                              <small>
                                <strong>💡 Recommended Action:</strong>
                                <br />
                                {urgency.action}
                              </small>
                            </div>
                          </div>
                          {alert.acknowledged_by && (
                            <div className="mt-2">
                              <small className="text-muted">
                                <strong>Acknowledged by:</strong> {alert.acknowledged_by}
                              </small>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Info and Help Section */}
      <div className="row mt-4">
        <div className="col-md-6">
          <div className="alert alert-info border-0 shadow-sm">
            <h6 className="alert-heading mb-2">
              💡 Alert Types Explained
            </h6>
            <small>
              <strong>⏰ Certificate Expiry:</strong> Warns about upcoming certificate
              expirations. Plan renewals at least 30 days in advance.
              <br />
              <strong>🔐 Crypto Weakness:</strong> Identifies cryptographic issues
              like weak keys, outdated algorithms, or self-signed certificates.
            </small>
          </div>
        </div>
        <div className="col-md-6">
          <div className="alert alert-success border-0 shadow-sm">
            <h6 className="alert-heading mb-2">
              🎯 Severity Levels
            </h6>
            <small>
              <strong>🔴 Critical:</strong> Requires immediate action.
              <br />
              <strong>🟠 High:</strong> Action recommended soon.
              <br />
              <strong>🟡 Medium/🟢 Low:</strong> Monitor for future action.
            </small>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AlertsPage
