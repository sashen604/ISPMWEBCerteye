import React, { useState, useEffect } from 'react'
import api from '../api'

function CertificatesPage() {
  // Main state
  const [certificates, setCertificates] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedCerts, setSelectedCerts] = useState(new Set())
  
  // Pagination state
  const [limit, setLimit] = useState(50)
  const [offset, setOffset] = useState(0)
  const [totalCount, setTotalCount] = useState(0)

  // Filter state
  const [search, setSearch] = useState('')
  const [riskLevel, setRiskLevel] = useState('')
  const [certType, setCertType] = useState('')
  const [sourceType, setSourceType] = useState('')
  const [expirationStatus, setExpirationStatus] = useState('')
  const [issuer, setIssuer] = useState('')
  const [keyLength, setKeyLength] = useState('')
  const [status, setStatus] = useState('')

  // Sorting state
  const [orderBy, setOrderBy] = useState('valid_to')

  // UI state
  const [detailCert, setDetailCert] = useState(null)
  const [statistics, setStatistics] = useState(null)
  const [message, setMessage] = useState({ type: '', text: '' })
  const [batchUpdateData, setBatchUpdateData] = useState({ status: '', source_priority: '' })

  // Load certificates
  const loadCertificates = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({
        limit,
        offset,
        ...(search && { search }),
        ...(riskLevel && { risk_level: riskLevel }),
        ...(certType && { certificate_type: certType }),
        ...(sourceType && { source_type: sourceType }),
        ...(expirationStatus && { expiration_status: expirationStatus }),
        ...(issuer && { issuer }),
        ...(keyLength && { key_length: keyLength }),
        ...(status && { status }),
        ordering: orderBy,
      })

      const response = await api.get(`/api/certificates/?${params}`)
      setCertificates(response.data.results || [])
      setTotalCount(response.data.count || 0)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load certificates')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  // Load statistics
  const loadStatistics = async () => {
    try {
      const response = await api.get('/api/certificates/statistics/')
      setStatistics(response.data)
    } catch (err) {
      console.error('Failed to load statistics:', err)
    }
  }

  // Initial load
  useEffect(() => {
    loadCertificates()
    loadStatistics()
  }, [limit, offset, search, riskLevel, certType, sourceType, expirationStatus, issuer, keyLength, status, orderBy])

  // Auto-dismiss messages
  useEffect(() => {
    if (message.text) {
      const timer = setTimeout(() => setMessage({ type: '', text: '' }), 3000)
      return () => clearTimeout(timer)
    }
  }, [message])

  // Toggle certificate selection
  const toggleCertSelect = (id) => {
    const newSelected = new Set(selectedCerts)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedCerts(newSelected)
  }

  // Select/deselect all
  const toggleAllSelect = () => {
    if (selectedCerts.size === certificates.length) {
      setSelectedCerts(new Set())
    } else {
      setSelectedCerts(new Set(certificates.map(c => c.id)))
    }
  }

  // Batch update
  const handleBatchUpdate = async () => {
    if (selectedCerts.size === 0) {
      setMessage({ type: 'error', text: 'Please select certificates to update' })
      return
    }

    if (!batchUpdateData.status && !batchUpdateData.source_priority) {
      setMessage({ type: 'error', text: 'Please select at least one field to update' })
      return
    }

    try {
      const updates = {}
      if (batchUpdateData.status) updates.status = batchUpdateData.status
      if (batchUpdateData.source_priority) updates.source_priority = parseInt(batchUpdateData.source_priority)

      const response = await api.post('/api/certificates/batch-update/', {
        certificate_ids: Array.from(selectedCerts),
        updates
      })

      setMessage({ type: 'success', text: `Updated ${response.data.updated_count} certificates` })
      setBatchUpdateData({ status: '', source_priority: '' })
      setSelectedCerts(new Set())
      setOffset(0)
    } catch (err) {
      setMessage({ type: 'error', text: err.response?.data?.error || 'Batch update failed' })
    }
  }

  // Export certificates
  const handleExport = async (format) => {
    try {
      const params = new URLSearchParams({ format })
      const response = await api.get(`/api/certificates/export/?${params}`, {
        responseType: format === 'json' ? 'json' : 'blob'
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `certificates.${format}`)
      document.body.appendChild(link)
      link.click()
      link.parentNode.removeChild(link)
    } catch (err) {
      setMessage({ type: 'error', text: 'Export failed' })
    }
  }

  // Helper functions
  const getRiskColor = (risk) => {
    switch (risk) {
      case 'CRITICAL': return '#dc2626'
      case 'HIGH': return '#ea580c'
      case 'MEDIUM': return '#f59e0b'
      case 'LOW': return '#16a34a'
      default: return '#6c757d'
    }
  }

  const getRiskEmoji = (risk) => {
    switch (risk) {
      case 'CRITICAL': return '🔴'
      case 'HIGH': return '🟠'
      case 'MEDIUM': return '🟡'
      case 'LOW': return '🟢'
      default: return '⚪'
    }
  }

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString()
  }

  const getDaysRemaining = (validTo) => {
    const days = Math.ceil((new Date(validTo) - new Date()) / (1000 * 60 * 60 * 24))
    return Math.max(0, days)
  }

  const totalPages = Math.ceil(totalCount / limit)
  const currentPage = Math.floor(offset / limit) + 1

  return (
    <div className="container-fluid">
      {/* Header */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h3 className="mb-0">📊 Certificate Inventory</h3>
          <small className="text-muted">Unified view of all public and internal certificates</small>
        </div>
        <div className="gap-2 d-flex">
          <button className="btn btn-outline-secondary btn-sm" onClick={() => handleExport('csv')}>📥 CSV</button>
          <button className="btn btn-outline-secondary btn-sm" onClick={() => handleExport('json')}>📥 JSON</button>
          <button className="btn btn-outline-primary btn-sm" onClick={loadCertificates}>🔄 Refresh</button>
        </div>
      </div>

      {/* Message alerts */}
      {message.text && (
        <div className={`alert alert-${message.type === 'error' ? 'danger' : 'success'} alert-dismissible fade show`}>
          {message.text}
          <button type="button" className="btn-close" onClick={() => setMessage({ type: '', text: '' })}></button>
        </div>
      )}

      {/* Statistics cards */}
      {statistics && (
        <div className="row mb-4">
          <div className="col-md-3">
            <div className="card text-center">
              <div className="card-body">
                <h4>{statistics.total_certificates}</h4>
                <small className="text-muted">Total Certificates</small>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="card text-center border-danger">
              <div className="card-body">
                <h4 style={{ color: '#dc2626' }}>{statistics.by_risk_level.CRITICAL}</h4>
                <small className="text-muted">Critical 🔴</small>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="card text-center border-warning">
              <div className="card-body">
                <h4 style={{ color: '#ea580c' }}>{statistics.by_risk_level.HIGH}</h4>
                <small className="text-muted">High 🟠</small>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="card text-center">
              <div className="card-body">
                <h4>{statistics.expiration_stats.expiring_soon}</h4>
                <small className="text-muted">Expiring Soon ⏰</small>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filter section */}
      <div className="card mb-4 p-3">
        <h6 className="mb-3">🔍 Filters & Search</h6>
        
        <div className="row g-2 mb-3">
          <div className="col-lg-6">
            <input
              type="text"
              className="form-control form-control-sm"
              placeholder="Search domain, hostname, issuer..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setOffset(0)
              }}
            />
          </div>
          <div className="col-lg-2">
            <select
              className="form-select form-select-sm"
              value={riskLevel}
              onChange={(e) => {
                setRiskLevel(e.target.value)
                setOffset(0)
              }}
            >
              <option value="">All Risk Levels</option>
              <option value="CRITICAL">🔴 Critical</option>
              <option value="HIGH">🟠 High</option>
              <option value="MEDIUM">🟡 Medium</option>
              <option value="LOW">🟢 Low</option>
            </select>
          </div>
          <div className="col-lg-2">
            <select
              className="form-select form-select-sm"
              value={expirationStatus}
              onChange={(e) => {
                setExpirationStatus(e.target.value)
                setOffset(0)
              }}
            >
              <option value="">All Status</option>
              <option value="active">✅ Active</option>
              <option value="expiring_soon">⏰ Expiring Soon</option>
              <option value="expired">❌ Expired</option>
            </select>
          </div>
          <div className="col-lg-2">
            <select
              className="form-select form-select-sm"
              value={sourceType}
              onChange={(e) => {
                setSourceType(e.target.value)
                setOffset(0)
              }}
            >
              <option value="">All Sources</option>
              <option value="scanner">🔍 Scanner</option>
              <option value="internal_agent">🖥️ Internal Agent</option>
            </select>
          </div>
        </div>

        {/* Advanced filters */}
        <details className="mb-2">
          <summary className="cursor-pointer text-primary">Advanced Filters</summary>
          <div className="row g-2 mt-2">
            <div className="col-md-3">
              <input
                type="text"
                className="form-control form-control-sm"
                placeholder="Filter by issuer..."
                value={issuer}
                onChange={(e) => {
                  setIssuer(e.target.value)
                  setOffset(0)
                }}
              />
            </div>
            <div className="col-md-3">
              <select
                className="form-select form-select-sm"
                value={certType}
                onChange={(e) => {
                  setCertType(e.target.value)
                  setOffset(0)
                }}
              >
                <option value="">All Types</option>
                <option value="wildcard">Wildcard</option>
                <option value="self-signed">Self-Signed</option>
                <option value="single">Single</option>
                <option value="multi-domain">Multi-Domain</option>
              </select>
            </div>
            <div className="col-md-3">
              <select
                className="form-select form-select-sm"
                value={keyLength}
                onChange={(e) => {
                  setKeyLength(e.target.value)
                  setOffset(0)
                }}
              >
                <option value="">All Key Lengths</option>
                <option value="2048">2048-bit</option>
                <option value="4096">4096-bit</option>
                <option value="3072">3072-bit</option>
              </select>
            </div>
            <div className="col-md-3">
              <button
                className="btn btn-sm btn-outline-secondary w-100"
                onClick={() => {
                  setSearch('')
                  setRiskLevel('')
                  setCertType('')
                  setSourceType('')
                  setExpirationStatus('')
                  setIssuer('')
                  setKeyLength('')
                  setStatus('')
                  setOffset(0)
                }}
              >
                Clear Filters
              </button>
            </div>
          </div>
        </details>
      </div>

      {/* Batch operations */}
      {selectedCerts.size > 0 && (
        <div className="alert alert-info mb-3">
          <div className="row align-items-center">
            <div className="col">
              <strong>{selectedCerts.size} certificate(s) selected</strong>
            </div>
            <div className="col">
              <div className="row g-1">
                <div className="col-auto">
                  <select
                    className="form-select form-select-sm"
                    value={batchUpdateData.status}
                    onChange={(e) => setBatchUpdateData({ ...batchUpdateData, status: e.target.value })}
                  >
                    <option value="">Select status...</option>
                    <option value="active">Active</option>
                    <option value="archived">Archived</option>
                  </select>
                </div>
                <div className="col-auto">
                  <select
                    className="form-select form-select-sm"
                    value={batchUpdateData.source_priority}
                    onChange={(e) => setBatchUpdateData({ ...batchUpdateData, source_priority: e.target.value })}
                  >
                    <option value="">Priority...</option>
                    <option value="100">Internal (100)</option>
                    <option value="50">Scanner (50)</option>
                  </select>
                </div>
                <div className="col-auto">
                  <button className="btn btn-sm btn-primary" onClick={handleBatchUpdate}>💾 Update</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Certificates table */}
      <div className="card">
        {loading ? (
          <div className="card-body text-center py-5">
            <div className="spinner-border text-primary"></div>
            <p className="mt-3 text-muted">Loading certificates...</p>
          </div>
        ) : error ? (
          <div className="card-body">
            <div className="alert alert-danger mb-0">{error}</div>
          </div>
        ) : certificates.length === 0 ? (
          <div className="card-body text-center py-5">
            <p className="text-muted">No certificates found. Try adjusting your filters.</p>
          </div>
        ) : (
          <>
            <div className="table-responsive">
              <table className="table table-hover mb-0 table-sm">
                <thead className="table-light">
                  <tr>
                    <th style={{ width: '40px' }}>
                      <input
                        type="checkbox"
                        checked={selectedCerts.size === certificates.length && certificates.length > 0}
                        onChange={toggleAllSelect}
                      />
                    </th>
                    <th>Domain</th>
                    <th>Hostname</th>
                    <th>Issuer</th>
                    <th>Type</th>
                    <th>Source</th>
                    <th style={{ cursor: 'pointer' }} onClick={() => setOrderBy(orderBy === 'valid_to' ? '-valid_to' : 'valid_to')}>
                      Risk {getRiskEmoji(riskLevel)}
                    </th>
                    <th>Expires</th>
                    <th>Days Left</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {certificates.map(cert => (
                    <tr key={cert.id}>
                      <td>
                        <input
                          type="checkbox"
                          checked={selectedCerts.has(cert.id)}
                          onChange={() => toggleCertSelect(cert.id)}
                        />
                      </td>
                      <td>
                        <strong>{cert.domain}</strong>
                      </td>
                      <td>{cert.hostname || '—'}</td>
                      <td><small>{cert.issuer}</small></td>
                      <td><small>{cert.certificate_type}</small></td>
                      <td>
                        <span className="badge bg-secondary">
                          {cert.source_type === 'scanner' ? '🔍' : '🖥️'} {cert.source_type}
                        </span>
                      </td>
                      <td>
                        <span style={{ color: getRiskColor(cert.risk_level) }}>
                          <strong>{getRiskEmoji(cert.risk_level)} {cert.risk_level}</strong>
                        </span>
                      </td>
                      <td>{formatDate(cert.valid_to)}</td>
                      <td>
                        <strong style={{ color: getDaysRemaining(cert.valid_to) <= 30 ? '#c77dff' : 'inherit' }}>
                          {getDaysRemaining(cert.valid_to)} days
                        </strong>
                      </td>
                      <td>
                        <span className={`badge ${cert.status === 'active' ? 'bg-success' : 'bg-secondary'}`}>
                          {cert.status}
                        </span>
                      </td>
                      <td>
                        <button
                          className="btn btn-link btn-sm"
                          onClick={() => setDetailCert(cert)}
                        >
                          📋 Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="card-footer d-flex justify-content-between align-items-center">
              <div>
                Showing {offset + 1} to {Math.min(offset + limit, totalCount)} of {totalCount} certificates
              </div>
              <div className="d-flex gap-2 align-items-center">
                <select
                  className="form-select form-select-sm"
                  style={{ width: '80px' }}
                  value={limit}
                  onChange={(e) => {
                    setLimit(parseInt(e.target.value))
                    setOffset(0)
                  }}
                >
                  <option value="25">25</option>
                  <option value="50">50</option>
                  <option value="100">100</option>
                </select>
                <nav>
                  <ul className="pagination pagination-sm mb-0">
                    <li className={`page-item ${offset === 0 ? 'disabled' : ''}`}>
                      <button
                        className="page-link"
                        onClick={() => setOffset(Math.max(0, offset - limit))}
                      >
                        Previous
                      </button>
                    </li>
                    <li className="page-item disabled">
                      <span className="page-link">{currentPage} / {totalPages}</span>
                    </li>
                    <li className={`page-item ${currentPage >= totalPages ? 'disabled' : ''}`}>
                      <button
                        className="page-link"
                        onClick={() => setOffset(offset + limit)}
                      >
                        Next
                      </button>
                    </li>
                  </ul>
                </nav>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Detail modal */}
      {detailCert && (
        <div className="modal d-block" style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Certificate Details</h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => setDetailCert(null)}
                ></button>
              </div>
              <div className="modal-body">
                <div className="row mb-3">
                  <div className="col-md-6">
                    <strong>Domain:</strong> {detailCert.domain}
                  </div>
                  <div className="col-md-6">
                    <strong>Hostname:</strong> {detailCert.hostname || '—'}
                  </div>
                </div>
                <div className="row mb-3">
                  <div className="col-md-6">
                    <strong>Issuer:</strong> {detailCert.issuer}
                  </div>
                  <div className="col-md-6">
                    <strong>Subject:</strong> {detailCert.subject}
                  </div>
                </div>
                <div className="row mb-3">
                  <div className="col-md-6">
                    <strong>Serial Number:</strong>
                    <br />
                    <small className="text-monospace">{detailCert.serial_number}</small>
                  </div>
                  <div className="col-md-6">
                    <strong>Thumbprint:</strong>
                    <br />
                    <small className="text-monospace">{detailCert.thumbprint || '—'}</small>
                  </div>
                </div>
                <div className="row mb-3">
                  <div className="col-md-6">
                    <strong>Key Length:</strong> {detailCert.key_length} bits
                  </div>
                  <div className="col-md-6">
                    <strong>Signature Algorithm:</strong> {detailCert.signature_algorithm}
                  </div>
                </div>
                <div className="row mb-3">
                  <div className="col-md-6">
                    <strong>Valid From:</strong> {formatDate(detailCert.valid_from)}
                  </div>
                  <div className="col-md-6">
                    <strong>Valid To:</strong> {formatDate(detailCert.valid_to)}
                  </div>
                </div>
                <div className="row mb-3">
                  <div className="col-md-6">
                    <strong>Risk Level:</strong>{' '}
                    <span style={{ color: getRiskColor(detailCert.risk_level) }}>
                      {getRiskEmoji(detailCert.risk_level)} {detailCert.risk_level}
                    </span>
                  </div>
                  <div className="col-md-6">
                    <strong>Risk Score:</strong> {detailCert.risk_score}/100
                  </div>
                </div>
                <div className="row mb-3">
                  <div className="col-md-6">
                    <strong>Source:</strong> {detailCert.source_type}
                  </div>
                  <div className="col-md-6">
                    <strong>Status:</strong> {detailCert.status}
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setDetailCert(null)}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CertificatesPage
