import { useState, useEffect } from 'react'
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '../api'
import '../styles/dashboard.css'

function DashboardPage() {
  const [summaryStats, setSummaryStats] = useState({
    total: 0,
    expired: 0,
    expiringSoon: 0,
    highRisk: 0
  })
  const [chartData, setChartData] = useState({
    expiryData: [],
    riskData: []
  })
  const [certificates, setCertificates] = useState([])
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [riskFilter, setRiskFilter] = useState('')
  const [page, setPage] = useState(1)

  // Load dashboard data
  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError('')
      console.log('[Dashboard] Loading statistics...')
      
      // Fetch statistics
      const statsResponse = await api.get('/api/certificates/statistics/')
      const statsData = statsResponse.data
      
      // Extract summary stats
      const byRiskLevel = statsData.by_risk_level || {}
      const expirationStats = statsData.expiration_stats || {}
      
      setSummaryStats({
        total: statsData.total_certificates || 0,
        expired: expirationStats.expired || 0,
        expiringSoon: expirationStats.expiring_soon || 0,
        highRisk: (byRiskLevel.CRITICAL || 0) + (byRiskLevel.HIGH || 0)
      })
      
      // Prepare chart data
      setChartData({
        expiryData: [
          { name: 'Expired', value: expirationStats.expired || 0, fill: '#dc3545' },
          { name: 'Expiring Soon', value: expirationStats.expiring_soon || 0, fill: '#ffc107' },
          { name: 'Active', value: expirationStats.active || 0, fill: '#28a745' }
        ],
        riskData: [
          { name: 'CRITICAL', value: byRiskLevel.CRITICAL || 0, fill: '#dc3545' },
          { name: 'HIGH', value: byRiskLevel.HIGH || 0, fill: '#fd7e14' },
          { name: 'MEDIUM', value: byRiskLevel.MEDIUM || 0, fill: '#ffc107' },
          { name: 'LOW', value: byRiskLevel.LOW || 0, fill: '#28a745' }
        ]
      })
      
      console.log('[Dashboard] Fetching certificates...')
      // Fetch certificates
      const certResponse = await api.get('/api/certificates/?limit=100')
      const certs = certResponse.data.results || certResponse.data || []
      setCertificates(certs)
      
      console.log('[Dashboard] Dashboard data loaded successfully')
    } catch (err) {
      console.error('[Dashboard] Failed to load dashboard:', err)
      setError(err.response?.data?.detail || err.message || 'Failed to load dashboard. Please ensure you are logged in.')
    } finally {
      setLoading(false)
    }
  }


  // Filter and search certificates
  const getFilteredCertificates = () => {
    return certificates.filter(cert => {
      const matchesSearch = cert.domain.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           cert.issuer.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesRisk = !riskFilter || cert.risk_level?.toUpperCase() === riskFilter
      return matchesSearch && matchesRisk
    })
  }

  const getRiskColor = (level) => {
    const colors = {
      'CRITICAL': '#dc3545',
      'HIGH': '#fd7e14',
      'MEDIUM': '#ffc107',
      'LOW': '#28a745'
    }
    return colors[level] || '#6c757d'
  }

  const getRiskEmoji = (level) => {
    const emojis = {
      'CRITICAL': '🔴',
      'HIGH': '🟠',
      'MEDIUM': '🟡',
      'LOW': '🟢'
    }
    return emojis[level] || '⚪'
  }

  const filteredCerts = getFilteredCertificates()
  const totalResults = filteredCerts.length

  return (
    <div className="dashboard-container">
      {/* Header */}
      <div className="dashboard-header">
        <div>
          <h2 className="dashboard-title">📊 Certificate Dashboard</h2>
          <p className="dashboard-subtitle">Overview of certificate health, risk assessment, and expiration tracking</p>
        </div>
        <button className="btn btn-primary" onClick={loadDashboardData} disabled={loading}>
          🔄 Refresh
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="alert alert-danger alert-dismissible fade show" role="alert">
          ⚠️ {error}
          <button type="button" className="btn-close" onClick={() => setError('')}></button>
        </div>
      )}

      {/* Loading State */}
      {loading && !error && (
        <div className="alert alert-info">
          ⏳ Loading dashboard data...
        </div>
      )}

      {!loading && (
        <>
          {/* Summary Cards */}
          <div className="row mb-4">
            <div className="col-md-6 col-lg-3 mb-3">
              <div className="summary-card card h-100">
                <div className="card-body">
                  <div className="card-icon">📋</div>
                  <h6 className="card-title">Total Certificates</h6>
                  <div className="card-value">{summaryStats.total}</div>
                </div>
              </div>
            </div>
            <div className="col-md-6 col-lg-3 mb-3">
              <div className="summary-card card h-100 expired">
                <div className="card-body">
                  <div className="card-icon">⏱️</div>
                  <h6 className="card-title">Expired</h6>
                  <div className="card-value">{summaryStats.expired}</div>
                </div>
              </div>
            </div>
            <div className="col-md-6 col-lg-3 mb-3">
              <div className="summary-card card h-100 expiring">
                <div className="card-body">
                  <div className="card-icon">⚠️</div>
                  <h6 className="card-title">Expiring Soon</h6>
                  <div className="card-value">{summaryStats.expiringSoon}</div>
                </div>
              </div>
            </div>
            <div className="col-md-6 col-lg-3 mb-3">
              <div className="summary-card card h-100 high-risk">
                <div className="card-body">
                  <div className="card-icon">🔴</div>
                  <h6 className="card-title">High Risk</h6>
                  <div className="card-value">{summaryStats.highRisk}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Charts Row */}
          <div className="row mb-4">
            <div className="col-md-6">
              <div className="card h-100">
                <div className="card-header bg-light">
                  <h6 className="mb-0">Certificate Expiry Distribution</h6>
                </div>
                <div className="card-body d-flex justify-content-center">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={chartData.expiryData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                        {chartData.expiryData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
            <div className="col-md-6">
              <div className="card h-100">
                <div className="card-header bg-light">
                  <h6 className="mb-0">Risk Level Distribution</h6>
                </div>
                <div className="card-body d-flex justify-content-center">
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={chartData.riskData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, value }) => `${name}: ${value}`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {chartData.riskData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>

          {/* Certificate Inventory */}
          <div className="card mb-4">
            <div className="card-header bg-light">
              <h6 className="mb-0">📜 Certificate Inventory</h6>
            </div>
            <div className="card-body">
              {/* Search and Filter */}
              <div className="row mb-3 g-2">
                <div className="col-md-8">
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Search by domain or issuer..."
                    value={searchTerm}
                    onChange={(e) => {
                      setSearchTerm(e.target.value)
                      setPage(1)
                    }}
                  />
                </div>
                <div className="col-md-4">
                  <select
                    className="form-select"
                    value={riskFilter}
                    onChange={(e) => {
                      setRiskFilter(e.target.value)
                      setPage(1)
                    }}
                  >
                    <option value="">All Risk Levels</option>
                    <option value="CRITICAL">🔴 CRITICAL</option>
                    <option value="HIGH">🟠 HIGH</option>
                    <option value="MEDIUM">🟡 MEDIUM</option>
                    <option value="LOW">🟢 LOW</option>
                  </select>
                </div>
              </div>

              {/* Results Info */}
              <p className="text-muted small mb-3">
                Showing {filteredCerts.length} of {certificates.length} certificates
              </p>

              {/* Certificate Table */}
              <div className="table-responsive">
                <table className="table table-hover mb-0">
                  <thead>
                    <tr className="table-light">
                      <th>Domain</th>
                      <th>Issuer</th>
                      <th>Risk Level</th>
                      <th>Score</th>
                      <th>Expires</th>
                      <th>Days Left</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredCerts.length > 0 ? (
                      filteredCerts.slice((page - 1) * 10, page * 10).map((cert) => {
                        const daysLeft = cert.days_remaining || 0
                        const isExpired = daysLeft < 0
                        const isExpiringSoon = daysLeft >= 0 && daysLeft <= 30
                        
                        return (
                          <tr key={cert.id}>
                            <td>
                              <span className="font-monospace">{cert.domain}</span>
                            </td>
                            <td className="text-truncate" title={cert.issuer}>{cert.issuer}</td>
                            <td>
                              <span 
                                className="badge"
                                style={{ backgroundColor: getRiskColor(cert.risk_level) }}
                              >
                                {getRiskEmoji(cert.risk_level)} {cert.risk_level}
                              </span>
                            </td>
                            <td>
                              <span className="badge bg-secondary">{cert.risk_score}/100</span>
                            </td>
                            <td>{new Date(cert.valid_to).toLocaleDateString()}</td>
                            <td>
                              <span className={`badge ${isExpired ? 'bg-danger' : isExpiringSoon ? 'bg-warning text-dark' : 'bg-success'}`}>
                                {isExpired ? 'EXPIRED' : `${daysLeft}d`}
                              </span>
                            </td>
                          </tr>
                        )
                      })
                    ) : (
                      <tr>
                        <td colSpan="6" className="text-center text-muted py-4">
                          No certificates found. {searchTerm || riskFilter ? 'Try adjusting your filters.' : 'Scan a domain to get started!'}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {filteredCerts.length > 10 && (
                <nav className="mt-3" aria-label="Page navigation">
                  <ul className="pagination justify-content-center mb-0">
                    <li className={`page-item ${page === 1 ? 'disabled' : ''}`}>
                      <button className="page-link" onClick={() => setPage(p => p - 1)} disabled={page === 1}>
                        Previous
                      </button>
                    </li>
                    <li className="page-item active">
                      <span className="page-link">Page {page}</span>
                    </li>
                    <li className={`page-item ${page * 10 >= filteredCerts.length ? 'disabled' : ''}`}>
                      <button className="page-link" onClick={() => setPage(p => p + 1)} disabled={page * 10 >= filteredCerts.length}>
                        Next
                      </button>
                    </li>
                  </ul>
                </nav>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default DashboardPage
