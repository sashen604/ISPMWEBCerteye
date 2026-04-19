import React, { useState } from 'react'
import { exportApi } from '../api'

function ExportPage() {
  const [exportType, setExportType] = useState('all')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })
  
  // Filter options for different export types
  const [filterOptions, setFilterOptions] = useState({
    days: 30,           // For expiring
    threshold: 60,      // For high-risk (risk score)
    issuer: '',         // For by-issuer
    customFilters: {}   // For custom
  })

  const exportScenarios = [
    {
      id: 'all',
      title: 'All Certificates',
      description: 'Export all certificates in your inventory',
      icon: '📋',
      needsParams: false
    },
    {
      id: 'expiring',
      title: 'Expiring Certificates',
      description: 'Export certificates expiring within N days',
      icon: '⏰',
      needsParams: true,
      params: {
        days: { label: 'Days until expiry', type: 'number', default: 30, min: 1 }
      }
    },
    {
      id: 'high_risk',
      title: 'High-Risk Certificates',
      description: 'Export certificates with risk score above threshold',
      icon: '⚠️',
      needsParams: true,
      params: {
        threshold: { label: 'Risk score threshold (0-100)', type: 'number', default: 60, min: 0, max: 100 }
      }
    },
    {
      id: 'by_issuer',
      title: 'By Issuer',
      description: 'Export certificates from a specific issuer',
      icon: '🏢',
      needsParams: true,
      params: {
        issuer: { label: 'Issuer name', type: 'text', default: 'Let\'s Encrypt' }
      }
    },
    {
      id: 'critical',
      title: 'Critical Alerts',
      description: 'Export certificates with critical security alerts',
      icon: '🔴',
      needsParams: false
    },
    {
      id: 'custom',
      title: 'Custom Filter',
      description: 'Export with advanced filtering options',
      icon: '⚙️',
      needsParams: true,
      params: {
        status: { label: 'Status (active/expired/revoked)', type: 'text', default: 'active' },
        keyLength: { label: 'Minimum key length', type: 'number', default: 2048 }
      }
    }
  ]

  const handleExport = async (scenario) => {
    setLoading(true)
    setMessage({ type: '', text: '' })
    
    try {
      const scenario_obj = exportScenarios.find(s => s.id === scenario)
      const params = {}

      // Add relevant parameters based on export type
      if (scenario === 'expiring') {
        params.days = filterOptions.days
      } else if (scenario === 'high_risk') {
        params.threshold = filterOptions.threshold
      } else if (scenario === 'by_issuer') {
        params.issuer = filterOptions.issuer
      } else if (scenario === 'custom') {
        params.status = filterOptions.customFilters.status || 'active'
        params.key_length = filterOptions.customFilters.keyLength || 2048
      }

      const blob = await exportApi.exportCertificates(scenario, params)
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([blob]))
      const link = document.createElement('a')
      link.href = url
      const timestamp = new Date().toISOString().split('T')[0]
      link.setAttribute('download', `certificates_${scenario}_${timestamp}.csv`)
      document.body.appendChild(link)
      link.click()
      link.parentNode.removeChild(link)
      window.URL.revokeObjectURL(url)

      setMessage({ 
        type: 'success', 
        text: `✅ Successfully exported ${scenario_obj.title.toLowerCase()}. File downloaded.` 
      })
    } catch (err) {
      console.error('Export failed:', err)
      setMessage({ 
        type: 'error', 
        text: err.error || err.message || 'Failed to export certificates' 
      })
    } finally {
      setLoading(false)
    }
  }

  const currentScenario = exportScenarios.find(s => s.id === exportType)

  return (
    <div>
      {/* Header */}
      <div className="mb-4">
        <h3 className="mb-1">📊 Certificate Export</h3>
        <p className="text-muted">Download certificates in CSV format with advanced filtering options</p>
      </div>

      {/* Status Message */}
      {message.text && (
        <div className={`alert alert-${message.type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`} role="alert">
          {message.text}
          <button type="button" className="btn-close" onClick={() => setMessage({ type: '', text: '' })}></button>
        </div>
      )}

      <div className="row">
        {/* Left: Export Scenarios */}
        <div className="col-md-6">
          <div className="card mb-4">
            <div className="card-header bg-light">
              <h5 className="mb-0">Export Scenarios</h5>
            </div>
            <div className="card-body p-0">
              {exportScenarios.map(scenario => (
                <div
                  key={scenario.id}
                  className={`p-3 border-bottom cursor-pointer ${exportType === scenario.id ? 'bg-light border-left border-primary' : ''}`}
                  style={{
                    cursor: 'pointer',
                    borderLeft: exportType === scenario.id ? '4px solid #0d6efd' : 'none',
                    transition: 'all 0.2s'
                  }}
                  onClick={() => setExportType(scenario.id)}
                >
                  <div className="d-flex justify-content-between align-items-start">
                    <div className="flex-grow-1">
                      <div className="mb-1">
                        <span className="me-2">{scenario.icon}</span>
                        <strong>{scenario.title}</strong>
                      </div>
                      <small className="text-muted">{scenario.description}</small>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Configuration & Export */}
        <div className="col-md-6">
          <div className="card">
            <div className="card-header bg-light">
              <h5 className="mb-0">
                {currentScenario.icon} {currentScenario.title}
              </h5>
            </div>
            <div className="card-body">
              <p className="text-muted mb-4">{currentScenario.description}</p>

              {/* Configuration form for scenarios with parameters */}
              {currentScenario.needsParams && (
                <div className="mb-4">
                  <div className="card bg-light border-0 mb-3">
                    <div className="card-body">
                      {exportType === 'expiring' && (
                        <div>
                          <label className="form-label fw-bold">Days until expiry</label>
                          <div className="input-group">
                            <input
                              type="number"
                              className="form-control"
                              min="1"
                              value={filterOptions.days}
                              onChange={(e) => setFilterOptions({
                                ...filterOptions,
                                days: Math.max(1, parseInt(e.target.value) || 30)
                              })}
                            />
                            <span className="input-group-text">days</span>
                          </div>
                          <small className="text-muted d-block mt-2">
                            📌 Will export certificates expiring within {filterOptions.days} days
                          </small>
                        </div>
                      )}

                      {exportType === 'high_risk' && (
                        <div>
                          <label className="form-label fw-bold">Risk score threshold</label>
                          <div className="input-group">
                            <input
                              type="number"
                              className="form-control"
                              min="0"
                              max="100"
                              value={filterOptions.threshold}
                              onChange={(e) => setFilterOptions({
                                ...filterOptions,
                                threshold: Math.min(100, Math.max(0, parseInt(e.target.value) || 60))
                              })}
                            />
                            <span className="input-group-text">/ 100</span>
                          </div>
                          <small className="text-muted d-block mt-2">
                            📌 Will export certificates with risk score ≥ {filterOptions.threshold}
                          </small>
                        </div>
                      )}

                      {exportType === 'by_issuer' && (
                        <div>
                          <label className="form-label fw-bold">Issuer name</label>
                          <input
                            type="text"
                            className="form-control"
                            placeholder="e.g., Let's Encrypt, DigiCert, etc."
                            value={filterOptions.issuer}
                            onChange={(e) => setFilterOptions({
                              ...filterOptions,
                              issuer: e.target.value
                            })}
                          />
                          <small className="text-muted d-block mt-2">
                            📌 Will export certificates from: <strong>{filterOptions.issuer || 'any issuer'}</strong>
                          </small>
                        </div>
                      )}

                      {exportType === 'custom' && (
                        <div>
                          <div className="mb-3">
                            <label className="form-label fw-bold">Status</label>
                            <input
                              type="text"
                              className="form-control"
                              placeholder="e.g., active, expired, revoked"
                              value={filterOptions.customFilters.status || ''}
                              onChange={(e) => setFilterOptions({
                                ...filterOptions,
                                customFilters: { ...filterOptions.customFilters, status: e.target.value }
                              })}
                            />
                          </div>
                          <div>
                            <label className="form-label fw-bold">Minimum key length</label>
                            <div className="input-group">
                              <input
                                type="number"
                                className="form-control"
                                min="512"
                                step="512"
                                value={filterOptions.customFilters.keyLength || 2048}
                                onChange={(e) => setFilterOptions({
                                  ...filterOptions,
                                  customFilters: { ...filterOptions.customFilters, keyLength: parseInt(e.target.value) || 2048 }
                                })}
                              />
                              <span className="input-group-text">bits</span>
                            </div>
                          </div>
                          <small className="text-muted d-block mt-2">
                            📌 Will export {filterOptions.customFilters.status || 'active'} certificates with ≥{filterOptions.customFilters.keyLength || 2048} bit keys
                          </small>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Export button and info */}
              <div className="mb-3">
                <button
                  className="btn btn-primary w-100"
                  onClick={() => handleExport(exportType)}
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                      Exporting...
                    </>
                  ) : (
                    <>
                      ⬇️ Export as CSV
                    </>
                  )}
                </button>
              </div>

              {/* Export info */}
              <div className="alert alert-info alert-sm py-2 px-3 mb-0">
                <small>
                  <strong>💡 Format:</strong> CSV file with 17 columns including domain, issuer, expiry date, risk level, key length, and more.
                  <br />
                  <strong>📅 File name:</strong> <code>certificates_{exportType}_{new Date().toISOString().split('T')[0]}.csv</code>
                </small>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features info */}
      <div className="row mt-4">
        <div className="col-md-12">
          <div className="card bg-light border-0">
            <div className="card-body">
              <h6 className="mb-3">✨ Available Export Scenarios</h6>
              <div className="row">
                <div className="col-md-6">
                  <ul className="list-unstyled small">
                    <li className="mb-2">🎯 <strong>All Certificates:</strong> Complete inventory export</li>
                    <li className="mb-2">⏰ <strong>Expiring:</strong> Filter by expiry window</li>
                    <li className="mb-2">⚠️ <strong>High-Risk:</strong> By risk score threshold</li>
                  </ul>
                </div>
                <div className="col-md-6">
                  <ul className="list-unstyled small">
                    <li className="mb-2">🏢 <strong>By Issuer:</strong> Filter by CA provider</li>
                    <li className="mb-2">🔴 <strong>Critical Alerts:</strong> Security issues</li>
                    <li className="mb-2">⚙️ <strong>Custom Filter:</strong> Advanced options</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ExportPage
