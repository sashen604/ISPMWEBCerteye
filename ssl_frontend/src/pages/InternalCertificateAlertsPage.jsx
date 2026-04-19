import { useState, useEffect } from 'react'
import api from '../api'
import '../styles/admin-panel.css'

function InternalCertificateAlertsPage() {
  const [alertSettings, setAlertSettings] = useState({
    // Expiration alerts
    enable_expiration_alerts: true,
    expiration_threshold_days: 30,
    critical_threshold_days: 7,
    
    // Risk level alerts
    enable_critical_alerts: true,
    enable_high_alerts: true,
    enable_medium_alerts: false,
    
    // Notification settings
    notification_channels: {
      email: true,
      dashboard: true,
      webhook: false,
    },
    email_recipients: [],
    webhook_url: '',
    
    // Alert frequency
    alert_frequency: 'immediate', // immediate, daily, weekly
    
    // Monitored hostnames
    monitored_hostnames: [],
    all_hostnames: false,
  })

  const [availableHostnames, setAvailableHostnames] = useState([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })
  const [newEmail, setNewEmail] = useState('')
  const [testMode, setTestMode] = useState(false)

  // Load settings and available hostnames
  useEffect(() => {
    loadAlertSettings()
    loadAvailableHostnames()
  }, [])

  const loadAlertSettings = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/internal-certificates/alert-settings/')
      if (response.data) {
        setAlertSettings(response.data)
      }
    } catch (err) {
      console.log('Using default alert settings', err.message)
      // Use default settings on error
    } finally {
      setLoading(false)
    }
  }

  const loadAvailableHostnames = async () => {
    try {
      const response = await api.get('/api/certificates/', {
        params: { source_type: 'internal_agent' }
      })
      const certs = response.data.results || response.data || []
      const hostnames = [...new Set(certs.map(c => c.hostname).filter(Boolean))]
      setAvailableHostnames(hostnames.sort())
    } catch (err) {
      console.error('Failed to load hostnames:', err)
    }
  }

  const handleCheckboxChange = (field) => {
    setAlertSettings(prev => ({
      ...prev,
      [field]: !prev[field]
    }))
  }

  const handleChannelChange = (channel) => {
    setAlertSettings(prev => ({
      ...prev,
      notification_channels: {
        ...prev.notification_channels,
        [channel]: !prev.notification_channels[channel]
      }
    }))
  }

  const handleInputChange = (field, value) => {
    setAlertSettings(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const addEmailRecipient = () => {
    if (newEmail && newEmail.includes('@')) {
      setAlertSettings(prev => ({
        ...prev,
        email_recipients: [...new Set([...prev.email_recipients, newEmail])]
      }))
      setNewEmail('')
      setMessage({ type: 'success', text: 'Email added successfully' })
      setTimeout(() => setMessage({ type: '', text: '' }), 3000)
    } else {
      setMessage({ type: 'error', text: 'Please enter a valid email address' })
    }
  }

  const removeEmailRecipient = (email) => {
    setAlertSettings(prev => ({
      ...prev,
      email_recipients: prev.email_recipients.filter(e => e !== email)
    }))
  }

  const toggleHostname = (hostname) => {
    setAlertSettings(prev => {
      const monitored = prev.monitored_hostnames.includes(hostname)
        ? prev.monitored_hostnames.filter(h => h !== hostname)
        : [...prev.monitored_hostnames, hostname]
      return { ...prev, monitored_hostnames: monitored }
    })
  }

  const toggleAllHostnames = () => {
    setAlertSettings(prev => ({
      ...prev,
      all_hostnames: !prev.all_hostnames,
      monitored_hostnames: !prev.all_hostnames ? availableHostnames : []
    }))
  }

  const saveSettings = async () => {
    try {
      setSaving(true)
      await api.post('/api/internal-certificates/alert-settings/', alertSettings)
      setMessage({ type: 'success', text: 'Alert settings saved successfully!' })
      setTimeout(() => setMessage({ type: '', text: '' }), 3000)
    } catch (err) {
      setMessage({ 
        type: 'error', 
        text: err.response?.data?.detail || 'Failed to save settings' 
      })
    } finally {
      setSaving(false)
    }
  }

  const testAlerts = async () => {
    try {
      setTestMode(true)
      await api.post('/api/internal-certificates/test-alerts/', {})
      setMessage({ type: 'success', text: 'Test alert sent successfully!' })
      setTimeout(() => setMessage({ type: '', text: '' }), 3000)
    } catch (err) {
      setMessage({ 
        type: 'error', 
        text: err.response?.data?.detail || 'Failed to send test alert' 
      })
    } finally {
      setTestMode(false)
    }
  }

  if (loading) {
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
          <h2 className="mb-1">🔔 Internal Certificate Alerts</h2>
          <p className="text-muted mb-0">Configure alert settings for internal certificates</p>
        </div>
        <div className="gap-2 d-flex">
          <button 
            className="btn btn-outline-secondary"
            onClick={testAlerts}
            disabled={testMode}
          >
            {testMode ? '📤 Sending...' : '📤 Test Alerts'}
          </button>
          <button 
            className="btn btn-primary"
            onClick={saveSettings}
            disabled={saving}
          >
            {saving ? '💾 Saving...' : '💾 Save Settings'}
          </button>
        </div>
      </div>

      {/* Alert Messages */}
      {message.text && (
        <div className={`alert alert-${message.type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`}>
          {message.text}
          <button 
            type="button" 
            className="btn-close" 
            onClick={() => setMessage({ type: '', text: '' })}
          />
        </div>
      )}

      <div className="row">
        {/* Left Column: Expiration & Risk Alerts */}
        <div className="col-lg-6 mb-4">
          <div className="card card-stat p-4">
            <h5 className="card-title mb-3">⏰ Expiration Alerts</h5>
            
            <div className="form-check form-switch mb-3">
              <input 
                className="form-check-input" 
                type="checkbox" 
                id="enable_expiration"
                checked={alertSettings.enable_expiration_alerts}
                onChange={() => handleCheckboxChange('enable_expiration_alerts')}
              />
              <label className="form-check-label" htmlFor="enable_expiration">
                Enable expiration alerts
              </label>
            </div>

            <div className="mb-3">
              <label className="form-label">⚠️ Warning Threshold (days before expiry)</label>
              <input 
                type="number" 
                className="form-control"
                min="1"
                max="180"
                value={alertSettings.expiration_threshold_days}
                onChange={(e) => handleInputChange('expiration_threshold_days', parseInt(e.target.value))}
              />
              <small className="text-muted">Alert when certificate expires within this period</small>
            </div>

            <div className="mb-3">
              <label className="form-label">🔴 Critical Threshold (days before expiry)</label>
              <input 
                type="number" 
                className="form-control"
                min="1"
                max="30"
                value={alertSettings.critical_threshold_days}
                onChange={(e) => handleInputChange('critical_threshold_days', parseInt(e.target.value))}
              />
              <small className="text-muted">Alert as CRITICAL when certificate expires within this period</small>
            </div>

            <hr className="my-3" />

            <h5 className="card-title mb-3">📊 Risk Level Alerts</h5>

            <div className="form-check mb-2">
              <input 
                className="form-check-input" 
                type="checkbox" 
                id="enable_critical"
                checked={alertSettings.enable_critical_alerts}
                onChange={() => handleCheckboxChange('enable_critical_alerts')}
              />
              <label className="form-check-label" htmlFor="enable_critical">
                🔴 Alert on CRITICAL risk level
              </label>
            </div>

            <div className="form-check mb-2">
              <input 
                className="form-check-input" 
                type="checkbox" 
                id="enable_high"
                checked={alertSettings.enable_high_alerts}
                onChange={() => handleCheckboxChange('enable_high_alerts')}
              />
              <label className="form-check-label" htmlFor="enable_high">
                🟠 Alert on HIGH risk level
              </label>
            </div>

            <div className="form-check">
              <input 
                className="form-check-input" 
                type="checkbox" 
                id="enable_medium"
                checked={alertSettings.enable_medium_alerts}
                onChange={() => handleCheckboxChange('enable_medium_alerts')}
              />
              <label className="form-check-label" htmlFor="enable_medium">
                🟡 Alert on MEDIUM risk level
              </label>
            </div>
          </div>
        </div>

        {/* Right Column: Notification Settings */}
        <div className="col-lg-6 mb-4">
          <div className="card card-stat p-4">
            <h5 className="card-title mb-3">📢 Notification Channels</h5>

            <div className="form-check form-switch mb-3">
              <input 
                className="form-check-input" 
                type="checkbox" 
                id="channel_email"
                checked={alertSettings.notification_channels.email}
                onChange={() => handleChannelChange('email')}
              />
              <label className="form-check-label" htmlFor="channel_email">
                📧 Email Notifications
              </label>
            </div>

            <div className="form-check form-switch mb-3">
              <input 
                className="form-check-input" 
                type="checkbox" 
                id="channel_dashboard"
                checked={alertSettings.notification_channels.dashboard}
                onChange={() => handleChannelChange('dashboard')}
              />
              <label className="form-check-label" htmlFor="channel_dashboard">
                📱 Dashboard Notifications
              </label>
            </div>

            <div className="form-check form-switch mb-3">
              <input 
                className="form-check-input" 
                type="checkbox" 
                id="channel_webhook"
                checked={alertSettings.notification_channels.webhook}
                onChange={() => handleChannelChange('webhook')}
              />
              <label className="form-check-label" htmlFor="channel_webhook">
                🔗 Webhook Integration
              </label>
            </div>

            {alertSettings.notification_channels.webhook && (
              <div className="mb-3">
                <label className="form-label">Webhook URL</label>
                <input 
                  type="text" 
                  className="form-control"
                  placeholder="https://your-webhook-url.com/alerts"
                  value={alertSettings.webhook_url}
                  onChange={(e) => handleInputChange('webhook_url', e.target.value)}
                />
              </div>
            )}

            <hr className="my-3" />

            <h5 className="card-title mb-3">⏱️ Alert Frequency</h5>

            <div className="form-check mb-2">
              <input 
                className="form-check-input" 
                type="radio" 
                id="freq_immediate"
                value="immediate"
                checked={alertSettings.alert_frequency === 'immediate'}
                onChange={(e) => handleInputChange('alert_frequency', e.target.value)}
              />
              <label className="form-check-label" htmlFor="freq_immediate">
                ⚡ Immediate (as soon as detected)
              </label>
            </div>

            <div className="form-check mb-2">
              <input 
                className="form-check-input" 
                type="radio" 
                id="freq_daily"
                value="daily"
                checked={alertSettings.alert_frequency === 'daily'}
                onChange={(e) => handleInputChange('alert_frequency', e.target.value)}
              />
              <label className="form-check-label" htmlFor="freq_daily">
                📅 Daily Summary
              </label>
            </div>

            <div className="form-check">
              <input 
                className="form-check-input" 
                type="radio" 
                id="freq_weekly"
                value="weekly"
                checked={alertSettings.alert_frequency === 'weekly'}
                onChange={(e) => handleInputChange('alert_frequency', e.target.value)}
              />
              <label className="form-check-label" htmlFor="freq_weekly">
                📆 Weekly Summary
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Email Recipients Section */}
      {alertSettings.notification_channels.email && (
        <div className="row mb-4">
          <div className="col-lg-6">
            <div className="card card-stat p-4">
              <h5 className="card-title mb-3">📧 Email Recipients</h5>

              <div className="input-group mb-3">
                <input 
                  type="email" 
                  className="form-control"
                  placeholder="Enter email address"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addEmailRecipient()}
                />
                <button 
                  className="btn btn-outline-primary" 
                  onClick={addEmailRecipient}
                >
                  ➕ Add
                </button>
              </div>

              <div>
                {alertSettings.email_recipients.length === 0 ? (
                  <p className="text-muted">No email recipients added yet</p>
                ) : (
                  alertSettings.email_recipients.map((email, idx) => (
                    <div key={idx} className="badge bg-light text-dark me-2 mb-2 p-2">
                      {email}
                      <button 
                        className="btn-close btn-sm ms-2"
                        onClick={() => removeEmailRecipient(email)}
                        style={{ fontSize: '0.8rem' }}
                      />
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Monitored Hostnames */}
          <div className="col-lg-6">
            <div className="card card-stat p-4">
              <h5 className="card-title mb-3">🖥️ Monitored Hostnames</h5>

              <div className="form-check form-switch mb-3">
                <input 
                  className="form-check-input" 
                  type="checkbox" 
                  id="monitor_all"
                  checked={alertSettings.all_hostnames}
                  onChange={toggleAllHostnames}
                />
                <label className="form-check-label" htmlFor="monitor_all">
                  Monitor all hostnames
                </label>
              </div>

              {!alertSettings.all_hostnames && availableHostnames.length > 0 && (
                <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                  {availableHostnames.map(hostname => (
                    <div key={hostname} className="form-check mb-2">
                      <input 
                        className="form-check-input" 
                        type="checkbox" 
                        id={`host_${hostname}`}
                        checked={alertSettings.monitored_hostnames.includes(hostname)}
                        onChange={() => toggleHostname(hostname)}
                      />
                      <label className="form-check-label" htmlFor={`host_${hostname}`}>
                        {hostname}
                      </label>
                    </div>
                  ))}
                </div>
              )}

              {availableHostnames.length === 0 && (
                <p className="text-muted">No hostnames available yet</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default InternalCertificateAlertsPage
