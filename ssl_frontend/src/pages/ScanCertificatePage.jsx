import React, { useState, useEffect } from 'react'
import api from '../api'

function ScanCertificatePage() {
  const [domain, setDomain] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)
  const [scanResult, setScanResult] = useState(null)

  // Clear messages after 5 seconds
  useEffect(() => {
    if (error || success) {
      const timer = setTimeout(() => {
        setError(null)
        setSuccess(false)
      }, 5000)
      return () => clearTimeout(timer)
    }
  }, [error, success])

  const handleScan = async (e) => {
    e.preventDefault()
    
    if (!domain.trim()) {
      setError('Please enter a domain name')
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(false)
    setScanResult(null)

    try {
      // Clean domain: handle full URLs, www prefixes, etc.
      let cleanedDomain = domain.trim().toLowerCase()
      
      // Remove protocol if present
      if (cleanedDomain.includes('://')) {
        cleanedDomain = cleanedDomain.split('://')[1]
      }
      
      // Remove www. prefix
      if (cleanedDomain.startsWith('www.')) {
        cleanedDomain = cleanedDomain.substring(4)
      }
      
      // Remove trailing slashes and paths
      cleanedDomain = cleanedDomain.split('/')[0]
      
      // Remove port number if present
      cleanedDomain = cleanedDomain.split(':')[0]
      
      const response = await api.post('/api/certificates/scan/', {
        domain: cleanedDomain
      })

      if (response.data.success) {
        setScanResult(response.data.certificate)
        setSuccess(true)
        setDomain('')
      } else {
        setError(response.data.error || 'Failed to scan certificate')
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to scan certificate: ' + err.message)
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    try {
      return new Date(dateString).toLocaleDateString()
    } catch {
      return 'Invalid Date'
    }
  }

  const getRiskColor = (riskLevel) => {
    const colors = {
      'CRITICAL': '#dc3545',
      'HIGH': '#fd7e14',
      'MEDIUM': '#ffc107',
      'LOW': '#28a745',
      'INFO': '#17a2b8'
    }
    return colors[riskLevel] || '#6c757d'
  }

  return (
    <div className="container-fluid py-4">
      <div className="row">
        <div className="col-12">
          <div className="card">
            <div className="card-header">
              <h2 className="mb-0">📋 Scan Public Domain Certificate</h2>
            </div>
            <div className="card-body">
              {/* Scan Form */}
              <form onSubmit={handleScan} className="mb-4">
                <div className="row">
                  <div className="col-md-8">
                    <div className="input-group">
                      <input
                        type="text"
                        className="form-control form-control-lg"
                        placeholder="Domain or URL (e.g., google.com, https://www.example.com)"
                        value={domain}
                        onChange={(e) => setDomain(e.target.value)}
                        disabled={loading}
                      />
                      <button
                        type="submit"
                        className="btn btn-primary btn-lg"
                        disabled={loading}
                      >
                        {loading ? (
                          <>
                            <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                            Scanning...
                          </>
                        ) : (
                          <>
                            🔍 Scan Certificate
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </form>

              {/* Error Message */}
              {error && (
                <div className="alert alert-danger alert-dismissible fade show" role="alert">
                  ❌ <strong>Error:</strong> {error}
                  <button
                    type="button"
                    className="btn-close"
                    onClick={() => setError(null)}
                  ></button>
                </div>
              )}

              {/* Success Message */}
              {success && (
                <div className="alert alert-success alert-dismissible fade show" role="alert">
                  ✅ <strong>Success!</strong> Certificate scanned successfully
                  <button
                    type="button"
                    className="btn-close"
                    onClick={() => setSuccess(false)}
                  ></button>
                </div>
              )}

              {/* Scan Results */}
              {scanResult && (
                <div className="mt-4">
                  <h3>📊 Certificate Details</h3>
                  <div className="row">
                    <div className="col-md-6">
                      <div className="card mb-3">
                        <div className="card-body">
                          <h5 className="card-title">Domain Information</h5>
                          <table className="table table-sm">
                            <tbody>
                              <tr>
                                <td><strong>Domain:</strong></td>
                                <td>{scanResult.domain}</td>
                              </tr>
                              <tr>
                                <td><strong>Subject:</strong></td>
                                <td><small>{scanResult.subject}</small></td>
                              </tr>
                              <tr>
                                <td><strong>Issuer:</strong></td>
                                <td><small>{scanResult.issuer}</small></td>
                              </tr>
                              <tr>
                                <td><strong>Certificate Type:</strong></td>
                                <td>{scanResult.certificate_type}</td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>

                    <div className="col-md-6">
                      <div className="card mb-3">
                        <div className="card-body">
                          <h5 className="card-title">Validity Information</h5>
                          <table className="table table-sm">
                            <tbody>
                              <tr>
                                <td><strong>Valid From:</strong></td>
                                <td>{formatDate(scanResult.valid_from)}</td>
                              </tr>
                              <tr>
                                <td><strong>Expires:</strong></td>
                                <td>{formatDate(scanResult.valid_to)}</td>
                              </tr>
                              <tr>
                                <td><strong>Days Remaining:</strong></td>
                                <td>
                                  <span className={`badge ${scanResult.days_remaining <= 30 ? 'bg-danger' : scanResult.days_remaining <= 90 ? 'bg-warning' : 'bg-success'}`}>
                                    {scanResult.days_remaining} days
                                  </span>
                                </td>
                              </tr>
                              <tr>
                                <td><strong>Status:</strong></td>
                                <td>
                                  <span className="badge bg-info">{scanResult.status}</span>
                                </td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="row">
                    <div className="col-md-6">
                      <div className="card mb-3">
                        <div className="card-body">
                          <h5 className="card-title">Security Information</h5>
                          <table className="table table-sm">
                            <tbody>
                              <tr>
                                <td><strong>Risk Level:</strong></td>
                                <td>
                                  <span 
                                    className="badge"
                                    style={{ backgroundColor: getRiskColor(scanResult.risk_level) }}
                                  >
                                    {scanResult.risk_level}
                                  </span>
                                </td>
                              </tr>
                              <tr>
                                <td><strong>Risk Score:</strong></td>
                                <td>
                                  <span className="badge bg-secondary">{scanResult.risk_score}/100</span>
                                </td>
                              </tr>
                              <tr>
                                <td><strong>Key Algorithm:</strong></td>
                                <td>{scanResult.signature_algorithm}</td>
                              </tr>
                              <tr>
                                <td><strong>Key Length:</strong></td>
                                <td>{scanResult.key_length} bits</td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>

                    <div className="col-md-6">
                      <div className="card mb-3">
                        <div className="card-body">
                          <h5 className="card-title">Technical Information</h5>
                          <table className="table table-sm">
                            <tbody>
                              <tr>
                                <td><strong>Serial Number:</strong></td>
                                <td><small>{scanResult.serial_number}</small></td>
                              </tr>
                              <tr>
                                <td><strong>Source:</strong></td>
                                <td>{scanResult.source_type}</td>
                              </tr>
                              <tr>
                                <td><strong>Last Scanned:</strong></td>
                                <td>{formatDate(scanResult.last_scanned)}</td>
                              </tr>
                              <tr>
                                <td><strong>Certificate ID:</strong></td>
                                <td><small>{scanResult.id}</small></td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Information Panel */}
              <div className="alert alert-info mt-4">
                <h5>ℹ️ About Certificate Scanning</h5>
                <ul className="mb-0">
                  <li>Enter any domain name (e.g., <code>google.com</code>) or full URL (e.g., <code>https://www.google.com/</code>)</li>
                  <li>Supports various formats: plain domains, URLs with https://, www prefixes, and port numbers</li>
                  <li>The system will automatically clean and parse the input to extract the domain</li>
                  <li>All certificates are stored in the database for monitoring and trend analysis</li>
                  <li>Risk scores are calculated based on expiration date, key length, and algorithm strength</li>
                  <li>You can export all scanned certificates from the Export page for reporting</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ScanCertificatePage
