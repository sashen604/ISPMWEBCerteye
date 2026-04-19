import { useState, useEffect } from 'react'
import api from '../api'
import '../styles/admin-panel.css'

function InternalCertificatesPage() {
  const [certificates, setCertificates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedHostname, setSelectedHostname] = useState(null)
  const [selectedTemplate, setSelectedTemplate] = useState(null)
  const [searchDomain, setSearchDomain] = useState('')

  const [hostnames, setHostnames] = useState([])
  const [templates, setTemplates] = useState([])
  const [stats, setStats] = useState({
    total: 0,
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    expiring: 0,
  })

  // Load internal certificates
  useEffect(() => {
    loadInternalCertificates()
  }, [])

  const loadInternalCertificates = async () => {
    try {
      setLoading(true)
      setError('')
      console.log('[InternalCerts] Fetching internal certificates...')

      const response = await api.get('/api/certificates/', {
        params: {
          source_type: 'internal_agent',
        },
      })

      const certs = response.data.results || response.data || []
      console.log('[InternalCerts] Loaded', certs.length, 'certificates')

      setCertificates(certs)

      // Extract unique hostnames and templates
      const uniqueHostnames = [...new Set(certs.map(c => c.hostname).filter(Boolean))]
      const uniqueTemplates = [...new Set(certs.map(c => c.template_name).filter(Boolean))]

      setHostnames(uniqueHostnames.sort())
      setTemplates(uniqueTemplates.sort())

      // Calculate stats
      const statsData = {
        total: certs.length,
        critical: certs.filter(c => c.risk_level === 'CRITICAL').length,
        high: certs.filter(c => c.risk_level === 'HIGH').length,
        medium: certs.filter(c => c.risk_level === 'MEDIUM').length,
        low: certs.filter(c => c.risk_level === 'LOW').length,
        expiring: certs.filter(c => c.days_remaining <= 30 && c.days_remaining > 0).length,
      }
      setStats(statsData)
    } catch (err) {
      console.error('[InternalCerts] Failed to load certificates:', err)
      setError(err.response?.data?.detail || 'Failed to load internal certificates')
    } finally {
      setLoading(false)
    }
  }

  const getFilteredCertificates = () => {
    return certificates.filter(cert => {
      if (selectedHostname && cert.hostname !== selectedHostname) return false
      if (selectedTemplate && cert.template_name !== selectedTemplate) return false
      if (searchDomain && !cert.domain.toLowerCase().includes(searchDomain.toLowerCase())) {
        return false
      }
      return true
    })
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

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const filteredCerts = getFilteredCertificates()

  return (
    <div style={styles.container}>
      {/* Sidebar Filters */}
      <div style={styles.sidebar}>
        <h3 style={styles.sidebarTitle}>🔍 Filters</h3>

        {/* Search Domain */}
        <div style={styles.filterSection}>
          <label style={styles.filterLabel}>Search Domain</label>
          <input
            type="text"
            placeholder="Search..."
            value={searchDomain}
            onChange={(e) => setSearchDomain(e.target.value)}
            style={styles.filterInput}
          />
        </div>

        {/* Hostname Filter */}
        <div style={styles.filterSection}>
          <label style={styles.filterLabel}>
            Hostname {hostnames.length > 0 && `(${hostnames.length})`}
          </label>
          <div style={styles.filterCheckboxes}>
            <label style={styles.checkbox}>
              <input
                type="radio"
                name="hostname"
                value=""
                checked={selectedHostname === null}
                onChange={() => setSelectedHostname(null)}
              />
              All Hostnames
            </label>
            {hostnames.map(hostname => (
              <label key={hostname} style={styles.checkbox}>
                <input
                  type="radio"
                  name="hostname"
                  value={hostname}
                  checked={selectedHostname === hostname}
                  onChange={() => setSelectedHostname(hostname)}
                />
                {hostname}
              </label>
            ))}
          </div>
        </div>

        {/* Template Filter */}
        <div style={styles.filterSection}>
          <label style={styles.filterLabel}>
            Certificate Template {templates.length > 0 && `(${templates.length})`}
          </label>
          <div style={styles.filterCheckboxes}>
            <label style={styles.checkbox}>
              <input
                type="radio"
                name="template"
                value=""
                checked={selectedTemplate === null}
                onChange={() => setSelectedTemplate(null)}
              />
              All Templates
            </label>
            {templates.map(template => (
              <label key={template} style={styles.checkbox}>
                <input
                  type="radio"
                  name="template"
                  value={template}
                  checked={selectedTemplate === template}
                  onChange={() => setSelectedTemplate(template)}
                />
                {template}
              </label>
            ))}
          </div>
        </div>

        {/* Risk Level Summary */}
        <div style={styles.filterSection}>
          <label style={styles.filterLabel}>Risk Level</label>
          <div style={styles.statsBox}>
            <div style={styles.statItem}>
              <span style={{ color: getRiskColor('CRITICAL') }}>🔴 Critical:</span>
              <strong>{stats.critical}</strong>
            </div>
            <div style={styles.statItem}>
              <span style={{ color: getRiskColor('HIGH') }}>🟠 High:</span>
              <strong>{stats.high}</strong>
            </div>
            <div style={styles.statItem}>
              <span style={{ color: getRiskColor('MEDIUM') }}>🟡 Medium:</span>
              <strong>{stats.medium}</strong>
            </div>
            <div style={styles.statItem}>
              <span style={{ color: getRiskColor('LOW') }}>🟢 Low:</span>
              <strong>{stats.low}</strong>
            </div>
          </div>
        </div>

        {/* Expiring Soon */}
        <div style={styles.filterSection}>
          <label style={styles.filterLabel}>⏰ Expiring Soon</label>
          <div style={styles.expiringBox}>
            <strong>{stats.expiring}</strong> certificates expiring within 30 days
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={styles.mainContent}>
        {/* Header */}
        <div style={styles.header}>
          <div>
            <h2 style={styles.title}>🖥️ Internal Certificates</h2>
            <p style={styles.subtitle}>Certificates collected from Windows systems via PowerShell agents</p>
          </div>
          <button
            style={styles.refreshBtn}
            onClick={loadInternalCertificates}
            disabled={loading}
          >
            🔄 Refresh
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div style={styles.alertError}>
            ⚠️ {error}
          </div>
        )}

        {/* Loading State */}
        {loading && !error && (
          <div style={styles.alertInfo}>
            ⏳ Loading internal certificates...
          </div>
        )}

        {/* Stats Bar */}
        {!loading && !error && (
          <div style={styles.statsBar}>
            <div style={styles.statCard}>
              <div style={styles.statValue}>{stats.total}</div>
              <div style={styles.statLabel}>Total Certificates</div>
            </div>
            <div style={styles.statCard}>
              <div style={{ ...styles.statValue, color: getRiskColor('CRITICAL') }}>{stats.critical}</div>
              <div style={styles.statLabel}>Critical</div>
            </div>
            <div style={styles.statCard}>
              <div style={{ ...styles.statValue, color: getRiskColor('HIGH') }}>{stats.high}</div>
              <div style={styles.statLabel}>High Risk</div>
            </div>
            <div style={styles.statCard}>
              <div style={{ ...styles.statValue, color: getRiskColor('MEDIUM') }}>{stats.medium}</div>
              <div style={styles.statLabel}>Medium</div>
            </div>
            <div style={styles.statCard}>
              <div style={{ ...styles.statValue, color: getRiskColor('LOW') }}>{stats.low}</div>
              <div style={styles.statLabel}>Low Risk</div>
            </div>
            <div style={styles.statCard}>
              <div style={styles.statValue} style={{ color: '#ff6b6b' }}>{stats.expiring}</div>
              <div style={styles.statLabel}>Expiring (30d)</div>
            </div>
          </div>
        )}

        {/* Certificates Table */}
        {!loading && !error && (
          <div style={styles.tableContainer}>
            {filteredCerts.length === 0 ? (
              <div style={styles.emptyState}>
                <p>No internal certificates found matching your filters</p>
              </div>
            ) : (
              <table style={styles.table}>
                <thead style={styles.tableHead}>
                  <tr>
                    <th style={styles.tableCell}>Hostname</th>
                    <th style={styles.tableCell}>Domain/Subject</th>
                    <th style={styles.tableCell}>Issuer</th>
                    <th style={styles.tableCell}>Template</th>
                    <th style={styles.tableCell}>Risk Level</th>
                    <th style={styles.tableCell}>Expires</th>
                    <th style={styles.tableCell}>Days Left</th>
                    <th style={styles.tableCell}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCerts.map((cert, idx) => (
                    <tr key={idx} style={styles.tableRow}>
                      <td style={styles.tableCell}>
                        <code style={styles.code}>{cert.hostname || 'N/A'}</code>
                      </td>
                      <td style={styles.tableCell}>
                        <small>{cert.domain}</small>
                      </td>
                      <td style={styles.tableCell}>
                        <small>{cert.issuer}</small>
                      </td>
                      <td style={styles.tableCell}>
                        <small>{cert.template_name || '-'}</small>
                      </td>
                      <td style={styles.tableCell}>
                        <span style={{
                          ...styles.badge,
                          backgroundColor: getRiskColor(cert.risk_level),
                          padding: '4px 8px',
                          borderRadius: '4px',
                          fontSize: '12px',
                        }}>
                          {getRiskEmoji(cert.risk_level)} {cert.risk_level}
                        </span>
                      </td>
                      <td style={styles.tableCell}>
                        <small>{formatDate(cert.valid_to)}</small>
                      </td>
                      <td style={{
                        ...styles.tableCell,
                        color: cert.days_remaining <= 30 ? '#ff6b6b' : 'inherit',
                        fontWeight: cert.days_remaining <= 30 ? 'bold' : 'normal',
                      }}>
                        <strong>{cert.days_remaining}</strong>
                      </td>
                      <td style={styles.tableCell}>
                        <small>{cert.status}</small>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// Styles
const styles = {
  container: {
    display: 'flex',
    height: '100vh',
    backgroundColor: '#0f0f1e',
  },
  sidebar: {
    width: '280px',
    backgroundColor: '#1a1a2e',
    borderRight: '1px solid #16213e',
    padding: '20px',
    overflowY: 'auto',
    maxHeight: '100vh',
  },
  sidebarTitle: {
    color: '#5b7cc4',
    fontSize: '16px',
    fontWeight: 'bold',
    marginBottom: '20px',
    paddingBottom: '10px',
    borderBottom: '1px solid #16213e',
  },
  filterSection: {
    marginBottom: '20px',
    paddingBottom: '15px',
    borderBottom: '1px solid #16213e',
  },
  filterLabel: {
    display: 'block',
    color: '#a0a0a0',
    fontSize: '12px',
    fontWeight: 'bold',
    textTransform: 'uppercase',
    marginBottom: '8px',
  },
  filterInput: {
    width: '100%',
    padding: '8px',
    backgroundColor: '#0f0f1e',
    border: '1px solid #16213e',
    borderRadius: '4px',
    color: '#e0e0e0',
    fontSize: '12px',
    fontFamily: 'monospace',
  },
  filterCheckboxes: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  checkbox: {
    display: 'flex',
    alignItems: 'center',
    color: '#a0a0a0',
    fontSize: '12px',
    cursor: 'pointer',
    gap: '6px',
  },
  statsBox: {
    backgroundColor: '#16213e',
    padding: '10px',
    borderRadius: '4px',
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  statItem: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '12px',
    color: '#e0e0e0',
  },
  expiringBox: {
    backgroundColor: '#16213e',
    padding: '10px',
    borderRadius: '4px',
    fontSize: '12px',
    color: '#ff6b6b',
    textAlign: 'center',
  },
  mainContent: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'auto',
    backgroundColor: '#0f0f1e',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px',
    borderBottom: '1px solid #16213e',
  },
  title: {
    color: '#e0e0e0',
    fontSize: '24px',
    margin: '0 0 4px 0',
  },
  subtitle: {
    color: '#a0a0a0',
    fontSize: '12px',
    margin: '0',
  },
  refreshBtn: {
    padding: '8px 16px',
    backgroundColor: '#5b7cc4',
    border: 'none',
    borderRadius: '4px',
    color: '#fff',
    cursor: 'pointer',
    fontSize: '12px',
    fontWeight: 'bold',
  },
  alertError: {
    margin: '20px',
    padding: '12px',
    backgroundColor: '#8b0000',
    border: '1px solid #ff0000',
    borderRadius: '4px',
    color: '#ff9999',
    fontSize: '12px',
  },
  alertInfo: {
    margin: '20px',
    padding: '12px',
    backgroundColor: '#1a3a52',
    border: '1px solid #3a6a92',
    borderRadius: '4px',
    color: '#7aafff',
    fontSize: '12px',
  },
  statsBar: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '12px',
    padding: '20px',
    backgroundColor: '#16213e',
    borderBottom: '1px solid #16213e',
  },
  statCard: {
    backgroundColor: '#1a1a2e',
    padding: '12px',
    borderRadius: '4px',
    textAlign: 'center',
  },
  statValue: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#5b7cc4',
  },
  statLabel: {
    fontSize: '11px',
    color: '#a0a0a0',
    marginTop: '4px',
  },
  tableContainer: {
    flex: 1,
    overflow: 'auto',
    padding: '20px',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    backgroundColor: '#1a1a2e',
    borderRadius: '4px',
    border: '1px solid #16213e',
  },
  tableHead: {
    backgroundColor: '#16213e',
    position: 'sticky',
    top: '0',
  },
  tableCell: {
    padding: '12px',
    textAlign: 'left',
    fontSize: '12px',
    color: '#e0e0e0',
    borderBottom: '1px solid #16213e',
  },
  tableRow: {
    borderBottom: '1px solid #16213e',
    transition: 'backgroundColor 0.2s',
  },
  code: {
    backgroundColor: '#0f0f1e',
    padding: '2px 6px',
    borderRadius: '3px',
    fontFamily: 'monospace',
    fontSize: '11px',
  },
  badge: {
    display: 'inline-block',
    padding: '4px 8px',
    borderRadius: '4px',
    fontSize: '11px',
    fontWeight: 'bold',
  },
  emptyState: {
    textAlign: 'center',
    padding: '40px',
    color: '#a0a0a0',
  },
}

export default InternalCertificatesPage
