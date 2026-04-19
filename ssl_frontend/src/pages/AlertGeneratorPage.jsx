import React, { useState, useEffect } from 'react'
import { alertApi } from '../api'

function AlertGeneratorPage() {
  const [alertTypes, setAlertTypes] = useState(['EXPIRY', 'CRYPTO_WEAKNESS'])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })
  const [generatedAlerts, setGeneratedAlerts] = useState(null)

  // Auto-dismiss messages
  useEffect(() => {
    if (message.text) {
      const timer = setTimeout(() => setMessage({ type: '', text: '' }), 5000)
      return () => clearTimeout(timer)
    }
  }, [message])

  const handleToggleAlertType = (type) => {
    setAlertTypes(prev =>
      prev.includes(type)
        ? prev.filter(t => t !== type)
        : [...prev, type]
    )
  }

  const handleGenerateAlerts = async () => {
    if (alertTypes.length === 0) {
      setMessage({ type: 'error', text: 'Please select at least one alert type' })
      return
    }

    setLoading(true)
    setMessage({ type: '', text: '' })

    try {
      const result = await alertApi.generateAlerts(alertTypes)

      setGeneratedAlerts(result)
      setMessage({
        type: 'success',
        text: `✅ Successfully generated alerts! Total: ${result.total_alerts || 0}`
      })
    } catch (err) {
      console.error('Failed to generate alerts:', err)
      setMessage({
        type: 'error',
        text: err.error || err.message || 'Failed to generate alerts. Ensure you have admin privileges.'
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-4">
        <h3 className="mb-1">⚡ Alert Generator</h3>
        <p className="text-muted">Manually trigger alert generation for certificate issues</p>
      </div>

      {/* Status Message */}
      {message.text && (
        <div className={`alert alert-${message.type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`} role="alert">
          {message.text}
          <button type="button" className="btn-close" onClick={() => setMessage({ type: '', text: '' })}></button>
        </div>
      )}

      <div className="row">
        {/* Left: Alert Type Selection */}
        <div className="col-md-6">
          <div className="card mb-4">
            <div className="card-header bg-light">
              <h5 className="mb-0">📋 Alert Types to Generate</h5>
            </div>
            <div className="card-body">
              <p className="text-muted mb-4">Select which types of alerts to generate:</p>

              <div className="mb-3">
                <div className="form-check p-3 border rounded mb-2" style={{ cursor: 'pointer' }}>
                  <input
                    className="form-check-input"
                    type="checkbox"
                    id="expiry"
                    checked={alertTypes.includes('EXPIRY')}
                    onChange={() => handleToggleAlertType('EXPIRY')}
                  />
                  <label className="form-check-label w-100" htmlFor="expiry" style={{ cursor: 'pointer' }}>
                    <div>
                      <strong>⏰ Certificate Expiry Alerts</strong>
                      <p className="text-muted mb-0 small mt-1">
                        Detect certificates expiring within configurable thresholds (7, 30, 90 days)
                      </p>
                    </div>
                  </label>
                </div>

                <div className="form-check p-3 border rounded" style={{ cursor: 'pointer' }}>
                  <input
                    className="form-check-input"
                    type="checkbox"
                    id="crypto"
                    checked={alertTypes.includes('CRYPTO_WEAKNESS')}
                    onChange={() => handleToggleAlertType('CRYPTO_WEAKNESS')}
                  />
                  <label className="form-check-label w-100" htmlFor="crypto" style={{ cursor: 'pointer' }}>
                    <div>
                      <strong>🔐 Cryptographic Weakness Alerts</strong>
                      <p className="text-muted mb-0 small mt-1">
                        Identify weak algorithms, insufficient key lengths, and self-signed certificates
                      </p>
                    </div>
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* Selected types summary */}
          {alertTypes.length > 0 && (
            <div className="card bg-light border-0 mb-4">
              <div className="card-body">
                <h6 className="mb-2">✓ Selected Alert Types:</h6>
                <div className="d-flex flex-wrap gap-2">
                  {alertTypes.includes('EXPIRY') && (
                    <span className="badge bg-primary">⏰ Expiry</span>
                  )}
                  {alertTypes.includes('CRYPTO_WEAKNESS') && (
                    <span className="badge bg-primary">🔐 Crypto Weakness</span>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right: Generation Controls */}
        <div className="col-md-6">
          <div className="card mb-4">
            <div className="card-header bg-light">
              <h5 className="mb-0">⚙️ Generate Alerts</h5>
            </div>
            <div className="card-body">
              <div className="alert alert-warning alert-sm mb-4">
                <small>
                  <strong>⚠️ Admin Only:</strong> This action requires administrative privileges and will scan all certificates in the system.
                </small>
              </div>

              <button
                className="btn btn-success w-100 mb-3"
                onClick={handleGenerateAlerts}
                disabled={loading || alertTypes.length === 0}
                style={{ padding: '12px 20px', fontSize: '16px' }}
              >
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    Generating Alerts...
                  </>
                ) : (
                  <>
                    ⚡ Generate Alerts Now
                  </>
                )}
              </button>

              <div className="alert alert-info alert-sm">
                <small>
                  <strong>💡 Process:</strong> The alert generator will:
                  <ul className="mb-0 mt-2 ps-3">
                    <li>Scan all certificates in your inventory</li>
                    <li>Check for selected alert conditions</li>
                    <li>Create new alerts for detected issues</li>
                    <li>Deduplicate within 24-hour window</li>
                    <li>Send email notifications to admins</li>
                  </ul>
                </small>
              </div>
            </div>
          </div>

          {/* Generation Results */}
          {generatedAlerts && (
            <div className="card border-success">
              <div className="card-header bg-success text-white">
                <h5 className="mb-0">✓ Generation Results</h5>
              </div>
              <div className="card-body">
                <div className="mb-3">
                  <div className="row">
                    <div className="col-6">
                      <div className="text-center">
                        <h4 className="text-success mb-0">{generatedAlerts.total_alerts || 0}</h4>
                        <small className="text-muted">Total Alerts</small>
                      </div>
                    </div>
                    <div className="col-6">
                      <div className="text-center">
                        <h4 className="text-info mb-0">{generatedAlerts.alerts?.length || 0}</h4>
                        <small className="text-muted">New Alerts</small>
                      </div>
                    </div>
                  </div>
                </div>

                {generatedAlerts.alerts && generatedAlerts.alerts.length > 0 && (
                  <div className="mt-3">
                    <h6 className="mb-2">Recent Alerts:</h6>
                    <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                      {generatedAlerts.alerts.slice(0, 5).map((alert, idx) => (
                        <div key={idx} className="p-2 border-bottom last:border-bottom-0 small">
                          <div className="d-flex justify-content-between">
                            <span className="fw-bold">{alert.certificate_domain || 'Unknown'}</span>
                            <span className={`badge bg-${alert.severity === 'CRITICAL' ? 'danger' : alert.severity === 'HIGH' ? 'warning' : 'info'}`}>
                              {alert.severity}
                            </span>
                          </div>
                          <small className="text-muted">{alert.message}</small>
                        </div>
                      ))}
                    </div>
                    {generatedAlerts.alerts.length > 5 && (
                      <small className="text-muted d-block mt-2">
                        +{generatedAlerts.alerts.length - 5} more alerts...
                      </small>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Alert Type Details */}
      <div className="row mt-4">
        <div className="col-md-12">
          <div className="card bg-light border-0">
            <div className="card-body">
              <h6 className="mb-3">📚 Alert Type Reference</h6>
              <div className="row">
                <div className="col-md-6">
                  <div className="mb-3">
                    <h6 className="mb-2">
                      <span className="me-2">⏰</span> Certificate Expiry Alerts
                    </h6>
                    <ul className="list-unstyled small ms-4">
                      <li>✓ 7-day warning (Critical)</li>
                      <li>✓ 30-day warning (High)</li>
                      <li>✓ 90-day warning (Medium)</li>
                    </ul>
                  </div>
                </div>
                <div className="col-md-6">
                  <div className="mb-3">
                    <h6 className="mb-2">
                      <span className="me-2">🔐</span> Cryptographic Weakness Alerts
                    </h6>
                    <ul className="list-unstyled small ms-4">
                      <li>✓ Self-signed certificates (High)</li>
                      <li>✓ Weak key algorithms (High)</li>
                      <li>✓ Insufficient key length (High)</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AlertGeneratorPage
