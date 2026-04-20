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
      'CRITICAL': '#dc2626',
      'HIGH': '#ea580c',
      'MEDIUM': '#f59e0b',
      'LOW': '#16a34a',
    }
    return colors[level] || '#0ea5e9'
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
              <div style={{ ...styles.statValue, color: '#FF6B6B' }}>{stats.expiring}</div>
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
                          color: '#ffffff',
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

// Styles - Enterprise Dashboard Theme
const styles = {
  container: {
    display: 'flex',
    gap: '20px',
    alignItems: 'flex-start',
    backgroundColor: 'transparent',
  },
  sidebar: {
    width: '300px',
    backgroundColor: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    boxShadow: 'var(--shadow)',
    padding: '20px',
    overflowY: 'auto',
    maxHeight: 'calc(100vh - 140px)',
  },
  sidebarTitle: {
    color: 'var(--text)',
    fontSize: '18px',
    fontWeight: '700',
    marginBottom: '20px',
    paddingBottom: '10px',
    borderBottom: '1px solid var(--border)',
  },
  filterSection: {
    marginBottom: '20px',
    paddingBottom: '15px',
    borderBottom: '1px solid var(--border)',
  },
  filterLabel: {
    display: 'block',
    color: 'var(--text-secondary)',
    fontSize: '13px',
    fontWeight: '600',
    textTransform: 'uppercase',
    marginBottom: '8px',
  },
  filterInput: {
    width: '100%',
    padding: '10px 12px',
    backgroundColor: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: '12px',
    color: 'var(--text)',
    fontSize: '13px',
  },
  filterCheckboxes: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  checkbox: {
    display: 'flex',
    alignItems: 'center',
    color: 'var(--text)',
    fontSize: '13px',
    cursor: 'pointer',
    gap: '6px',
  },
  statsBox: {
    backgroundColor: 'var(--surface-2)',
    padding: '10px',
    borderRadius: '12px',
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  statItem: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '13px',
    color: 'var(--text)',
  },
  expiringBox: {
    backgroundColor: 'rgba(220, 38, 38, 0.08)',
    padding: '10px',
    border: '1px solid rgba(220, 38, 38, 0.22)',
    borderRadius: '12px',
    fontSize: '13px',
    color: '#dc2626',
    textAlign: 'center',
  },
  mainContent: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'auto',
    minWidth: 0,
    gap: '16px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px',
    backgroundColor: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    boxShadow: 'var(--shadow)',
  },
  title: {
    color: 'var(--text)',
    fontSize: '28px',
    margin: '0 0 4px 0',
    fontWeight: '700',
  },
  subtitle: {
    color: 'var(--text-secondary)',
    fontSize: '13px',
    margin: '0',
  },
  refreshBtn: {
    padding: '10px 16px',
    backgroundColor: 'var(--primary)',
    border: 'none',
    borderRadius: '12px',
    color: '#ffffff',
    cursor: 'pointer',
    fontSize: '13px',
    fontWeight: '600',
    transition: 'all 0.3s ease',
  },
  alertError: {
    margin: '20px',
    padding: '12px',
    backgroundColor: 'rgba(255, 107, 107, 0.1)',
    border: '1px solid #FF6B6B',
    borderRadius: '4px',
    color: '#FF6B6B',
    fontSize: '12px',
  },
  alertInfo: {
    margin: '20px',
    padding: '12px',
    backgroundColor: 'rgba(14, 165, 233, 0.1)',
    border: '1px solid rgba(14, 165, 233, 0.28)',
    borderRadius: '12px',
    color: '#0369a1',
    fontSize: '12px',
  },
  statsBar: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '12px',
    padding: '2px',
  },
  statCard: {
    backgroundColor: 'var(--surface)',
    padding: '18px',
    borderRadius: 'var(--radius)',
    textAlign: 'left',
    border: '1px solid var(--border)',
    boxShadow: 'var(--shadow)',
  },
  statValue: {
    fontSize: '32px',
    fontWeight: '800',
    color: 'var(--text)',
  },
  statLabel: {
    fontSize: '13px',
    color: 'var(--text-secondary)',
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
    backgroundColor: 'var(--surface)',
    borderRadius: 'var(--radius)',
    border: '1px solid var(--border)',
    boxShadow: 'var(--shadow)',
  },
  tableHead: {
    backgroundColor: 'var(--surface-2)',
    position: 'sticky',
    top: '0',
  },
  tableCell: {
    padding: '12px',
    textAlign: 'left',
    fontSize: '13px',
    color: 'var(--text)',
    borderBottom: '1px solid #f1f5f9',
  },
  tableRow: {
    borderBottom: '1px solid #f1f5f9',
    transition: 'backgroundColor 0.2s',
  },
  code: {
    backgroundColor: 'var(--surface-2)',
    padding: '2px 6px',
    borderRadius: '8px',
    fontFamily: 'monospace',
    fontSize: '11px',
    color: 'var(--primary)',
  },
  badge: {
    display: 'inline-block',
    padding: '6px 10px',
    borderRadius: '999px',
    fontSize: '12px',
    fontWeight: '700',
  },
  emptyState: {
    textAlign: 'center',
    padding: '40px',
    color: 'var(--text-secondary)',
  },
}

export default InternalCertificatesPage
