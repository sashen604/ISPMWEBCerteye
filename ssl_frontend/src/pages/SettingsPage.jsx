import { useState, useEffect } from 'react'
import api from '../api'
import '../styles/settings.css'

function SettingsPage() {
  const [activeTab, setActiveTab] = useState('profile')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })
  const [user, setUser] = useState(null)

  // Profile form state
  const [profileData, setProfileData] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
  })

  // Password form state
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  })

  // Preferences form state
  const [preferences, setPreferences] = useState({
    alert_threshold_days: 30,
    notification_email: '',
    enable_email_alerts: true,
    enable_dashboard_alerts: true,
    dark_mode: false,
  })

  // Security settings state
  const [securitySettings, setSecuritySettings] = useState({
    enable_2fa: false,
    login_notifications: true,
    ip_whitelist: false,
    session_timeout: 30,
    password_expiry: 90,
    suspicious_login_alerts: true,
    api_key_rotation: 90,
  })

  // API Keys state
  const [apiKeys, setApiKeys] = useState([
    {
      id: 1,
      name: 'Production API Key',
      created: '2024-01-15',
      last_used: '2024-04-18',
      status: 'active',
    },
  ])

  // Security logs state
  const [securityLogs, setSecurityLogs] = useState([
    {
      id: 1,
      event: 'Password Changed',
      timestamp: '2024-04-19 14:30',
      status: 'success',
    },
    {
      id: 2,
      event: 'Login Attempt',
      timestamp: '2024-04-19 10:15',
      status: 'success',
    },
  ])

  // Fetch user profile on mount
  useEffect(() => {
    fetchProfile()
    fetchSecurityLogs()
  }, [])

  const fetchProfile = async () => {
    try {
      const response = await api.get('/api/auth/profile')
      const userData = response.data.user
      setUser(userData)
      setProfileData({
        username: userData.username || '',
        email: userData.email || '',
        first_name: userData.first_name || '',
        last_name: userData.last_name || '',
      })
      // Load security settings from API
      fetchSecuritySettings()
      // Load preferences from localStorage if available
      const savedPrefs = localStorage.getItem('userPreferences')
      if (savedPrefs) {
        setPreferences(JSON.parse(savedPrefs))
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load profile' })
    }
  }

  const fetchSecuritySettings = async () => {
    try {
      const response = await api.get('/api/auth/security/settings')
      setSecuritySettings(response.data.settings)
      localStorage.setItem('securitySettings', JSON.stringify(response.data.settings))
    } catch (error) {
      console.error('Failed to load security settings:', error)
    }
  }

  const fetchSecurityLogs = async () => {
    try {
      const response = await api.get('/api/auth/security/audit-logs?limit=10')
      if (response.data.logs && Array.isArray(response.data.logs)) {
        const formattedLogs = response.data.logs.map(log => ({
          id: log.id,
          event: log.event_type_display || log.event_type,
          timestamp: new Date(log.timestamp).toLocaleString(),
          status: log.status,
        }))
        setSecurityLogs(formattedLogs)
      }
    } catch (error) {
      console.error('Failed to load security logs:', error)
    }
  }

  const handleProfileChange = (e) => {
    const { name, value } = e.target
    setProfileData({ ...profileData, [name]: value })
  }

  const handlePasswordChange = (e) => {
    const { name, value } = e.target
    setPasswordData({ ...passwordData, [name]: value })
  }

  const handlePreferenceChange = (e) => {
    const { name, value, type, checked } = e.target
    setPreferences({
      ...preferences,
      [name]: type === 'checkbox' ? checked : value,
    })
  }

  const handleSecurityChange = (e) => {
    const { name, value, type, checked } = e.target
    setSecuritySettings({
      ...securitySettings,
      [name]: type === 'checkbox' ? checked : parseInt(value) || value,
    })
  }

  const updateProfile = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMessage({ type: '', text: '' })

    try {
      const response = await api.patch('/api/auth/profile/update/', profileData)
      setMessage({ type: 'success', text: 'Profile updated successfully!' })
      setUser(response.data.user)
      setTimeout(() => setMessage({ type: '', text: '' }), 3000)
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Failed to update profile',
      })
    } finally {
      setLoading(false)
    }
  }

  const updatePassword = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMessage({ type: '', text: '' })

    if (passwordData.new_password !== passwordData.confirm_password) {
      setMessage({ type: 'error', text: 'New passwords do not match' })
      setLoading(false)
      return
    }

    if (passwordData.new_password.length < 8) {
      setMessage({ type: 'error', text: 'Password must be at least 8 characters long' })
      setLoading(false)
      return
    }

    try {
      await api.post('/api/auth/change-password/', {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
      })
      setMessage({ type: 'success', text: 'Password changed successfully!' })
      setPasswordData({ current_password: '', new_password: '', confirm_password: '' })
      setTimeout(() => setMessage({ type: '', text: '' }), 3000)
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Failed to change password',
      })
    } finally {
      setLoading(false)
    }
  }

  const savePreferences = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMessage({ type: '', text: '' })

    try {
      localStorage.setItem('userPreferences', JSON.stringify(preferences))
      setMessage({ type: 'success', text: 'Preferences saved successfully!' })
      setTimeout(() => setMessage({ type: '', text: '' }), 3000)
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save preferences' })
    } finally {
      setLoading(false)
    }
  }

  const saveSecuritySettings = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMessage({ type: '', text: '' })

    try {
      await api.post('/api/auth/security-settings/', securitySettings)
      localStorage.setItem('securitySettings', JSON.stringify(securitySettings))
      setMessage({ type: 'success', text: 'Security settings updated successfully!' })
      setTimeout(() => setMessage({ type: '', text: '' }), 3000)
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Failed to save security settings',
      })
    } finally {
      setLoading(false)
    }
  }

  const generateNewApiKey = async () => {
    setLoading(true)
    try {
      const response = await api.post('/api/auth/generate-api-key/')
      const newKey = {
        id: response.data.id,
        name: `API Key ${new Date().toLocaleDateString()}`,
        created: new Date().toISOString().split('T')[0],
        last_used: 'Never',
        status: 'active',
      }
      setApiKeys([...apiKeys, newKey])
      setMessage({ type: 'success', text: 'API Key generated successfully! Save it in a secure location.' })
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to generate API key' })
    } finally {
      setLoading(false)
    }
  }

  const revokeApiKey = async (keyId) => {
    if (window.confirm('Are you sure you want to revoke this API key?')) {
      setLoading(true)
      try {
        await api.delete(`/api/auth/security/api-keys/${keyId}/`)
        setApiKeys(apiKeys.filter(key => key.id !== keyId))
        setMessage({ type: 'success', text: 'API key revoked successfully' })
        setTimeout(() => setMessage({ type: '', text: '' }), 3000)
      } catch (error) {
        setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to revoke API key' })
      } finally {
        setLoading(false)
      }
    }
  }

  const handleProfileUpdate = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const response = await api.patch('/api/auth/profile/', profileData)
      setUser(response.data.user)
      setMessage({ type: 'success', text: 'Profile updated successfully' })
      setTimeout(() => setMessage({ type: '', text: '' }), 3000)
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to update profile' })
    } finally {
      setLoading(false)
    }
  }

  const handleSecuritySettingsChange = (e) => {
    const { name, value, type, checked } = e.target
    setSecuritySettings({
      ...securitySettings,
      [name]: type === 'checkbox' ? checked : parseInt(value) || value,
    })
  }

  return (
    <div className="settings-container">
      <div className="settings-header">
        <div>
          <h3 className="mb-0">⚙️ Settings</h3>
          <p className="text-muted">Manage your account, security, and preferences</p>
        </div>
      </div>

      {message.text && (
        <div className={`alert alert-${message.type} alert-dismissible fade show`} role="alert">
          {message.text}
          <button
            type="button"
            className="btn-close"
            onClick={() => setMessage({ type: '', text: '' })}
          ></button>
        </div>
      )}

      <div className="settings-layout">
        {/* Tabs */}
        <div className="settings-tabs">
          <button
            className={`tab-button ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            👤 Profile
          </button>
          <button
            className={`tab-button ${activeTab === 'password' ? 'active' : ''}`}
            onClick={() => setActiveTab('password')}
          >
            🔐 Password
          </button>
          <button
            className={`tab-button ${activeTab === 'preferences' ? 'active' : ''}`}
            onClick={() => setActiveTab('preferences')}
          >
            🎨 Preferences
          </button>
          <button
            className={`tab-button ${activeTab === 'notifications' ? 'active' : ''}`}
            onClick={() => setActiveTab('notifications')}
          >
            🔔 Notifications
          </button>
          <button
            className={`tab-button ${activeTab === 'security' ? 'active' : ''}`}
            onClick={() => setActiveTab('security')}
          >
            🛡️ Security
          </button>
        </div>

        {/* Content */}
        <div className="settings-content">
          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <div className="settings-card">
              <h4 className="mb-4">👤 Profile Information</h4>
              <form onSubmit={handleProfileUpdate}>
                <div className="row g-3">
                  <div className="col-md-6">
                    <label className="form-label fw-bold">Username</label>
                    <input
                      type="text"
                      className="form-control"
                      name="username"
                      value={profileData.username}
                      disabled
                      style={{ backgroundColor: '#f5f5f5' }}
                    />
                    <small className="text-muted">Username cannot be changed</small>
                  </div>

                  <div className="col-md-6">
                    <label className="form-label fw-bold">Email Address</label>
                    <input
                      type="email"
                      className="form-control"
                      name="email"
                      value={profileData.email}
                      onChange={handleProfileChange}
                      required
                    />
                  </div>

                  <div className="col-md-6">
                    <label className="form-label fw-bold">First Name</label>
                    <input
                      type="text"
                      className="form-control"
                      name="first_name"
                      value={profileData.first_name}
                      onChange={handleProfileChange}
                    />
                  </div>

                  <div className="col-md-6">
                    <label className="form-label fw-bold">Last Name</label>
                    <input
                      type="text"
                      className="form-control"
                      name="last_name"
                      value={profileData.last_name}
                      onChange={handleProfileChange}
                    />
                  </div>

                  {user && (
                    <>
                      <div className="col-md-6">
                        <label className="form-label fw-bold">Role</label>
                        <input
                          type="text"
                          className="form-control"
                          value={user.role_display || 'User'}
                          disabled
                          style={{ backgroundColor: '#f5f5f5' }}
                        />
                      </div>

                      <div className="col-md-6">
                        <label className="form-label fw-bold">Member Since</label>
                        <input
                          type="text"
                          className="form-control"
                          value={
                            user.date_joined
                              ? new Date(user.date_joined).toLocaleDateString()
                              : 'N/A'
                          }
                          disabled
                          style={{ backgroundColor: '#f5f5f5' }}
                        />
                      </div>
                    </>
                  )}
                </div>

                <button type="submit" className="btn btn-primary mt-4" disabled={loading}>
                  {loading ? 'Updating...' : '💾 Save Changes'}
                </button>
              </form>
            </div>
          )}

          {/* Password Tab */}
          {activeTab === 'password' && (
            <div className="settings-card">
              <h4 className="mb-4">🔐 Change Password</h4>
              <form onSubmit={updatePassword}>
                <div className="row g-3">
                  <div className="col-12">
                    <label className="form-label fw-bold">Current Password</label>
                    <input
                      type="password"
                      className="form-control"
                      name="current_password"
                      value={passwordData.current_password}
                      onChange={handlePasswordChange}
                      required
                    />
                  </div>

                  <div className="col-12">
                    <label className="form-label fw-bold">New Password</label>
                    <input
                      type="password"
                      className="form-control"
                      name="new_password"
                      value={passwordData.new_password}
                      onChange={handlePasswordChange}
                      required
                      minLength="8"
                    />
                    <small className="text-muted">Minimum 8 characters</small>
                  </div>

                  <div className="col-12">
                    <label className="form-label fw-bold">Confirm New Password</label>
                    <input
                      type="password"
                      className="form-control"
                      name="confirm_password"
                      value={passwordData.confirm_password}
                      onChange={handlePasswordChange}
                      required
                      minLength="8"
                    />
                  </div>

                  <div className="col-12">
                    <div className="alert alert-info">
                      <strong>Password Requirements:</strong>
                      <ul className="mb-0 mt-2">
                        <li>At least 8 characters long</li>
                        <li>Mix of uppercase and lowercase letters</li>
                        <li>Include at least one number</li>
                        <li>Include at least one special character</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <button type="submit" className="btn btn-primary mt-4" disabled={loading}>
                  {loading ? 'Updating...' : '🔄 Change Password'}
                </button>
              </form>
            </div>
          )}

          {/* Preferences Tab */}
          {activeTab === 'preferences' && (
            <div className="settings-card">
              <h4 className="mb-4">🎨 Display Preferences</h4>
              <form onSubmit={savePreferences}>
                <div className="row g-3">
                  <div className="col-12">
                    <div className="form-check form-switch">
                      <input
                        className="form-check-input"
                        type="checkbox"
                        id="darkMode"
                        name="dark_mode"
                        checked={preferences.dark_mode}
                        onChange={handlePreferenceChange}
                      />
                      <label className="form-check-label" htmlFor="darkMode">
                        <strong>Dark Mode</strong>
                        <div className="text-muted" style={{ fontSize: '0.9em' }}>
                          Enable dark theme for easier viewing
                        </div>
                      </label>
                    </div>
                  </div>

                  <div className="col-12">
                    <hr />
                  </div>

                  <div className="col-md-6">
                    <label className="form-label fw-bold">Alert Threshold (days)</label>
                    <input
                      type="number"
                      className="form-control"
                      name="alert_threshold_days"
                      value={preferences.alert_threshold_days}
                      onChange={handlePreferenceChange}
                      min="1"
                      max="365"
                    />
                    <small className="text-muted">Warn when certificates expire within X days</small>
                  </div>

                  <div className="col-md-6">
                    <label className="form-label fw-bold">Items Per Page</label>
                    <select
                      className="form-control"
                      name="items_per_page"
                      value={preferences.items_per_page || 10}
                      onChange={handlePreferenceChange}
                    >
                      <option value="10">10 items</option>
                      <option value="25">25 items</option>
                      <option value="50">50 items</option>
                      <option value="100">100 items</option>
                    </select>
                  </div>
                </div>

                <button type="submit" className="btn btn-primary mt-4" disabled={loading}>
                  {loading ? 'Saving...' : '💾 Save Preferences'}
                </button>
              </form>
            </div>
          )}

          {/* Notifications Tab */}
          {activeTab === 'notifications' && (
            <div className="settings-card">
              <h4 className="mb-4">🔔 Notification Settings</h4>
              <form onSubmit={savePreferences}>
                <div className="row g-3">
                  <div className="col-12">
                    <div className="form-check form-switch">
                      <input
                        className="form-check-input"
                        type="checkbox"
                        id="emailAlerts"
                        name="enable_email_alerts"
                        checked={preferences.enable_email_alerts}
                        onChange={handlePreferenceChange}
                      />
                      <label className="form-check-label" htmlFor="emailAlerts">
                        <strong>Email Alerts</strong>
                        <div className="text-muted" style={{ fontSize: '0.9em' }}>
                          Receive alerts via email
                        </div>
                      </label>
                    </div>
                  </div>

                  <div className="col-12">
                    <div className="form-check form-switch">
                      <input
                        className="form-check-input"
                        type="checkbox"
                        id="dashboardAlerts"
                        name="enable_dashboard_alerts"
                        checked={preferences.enable_dashboard_alerts}
                        onChange={handlePreferenceChange}
                      />
                      <label className="form-check-label" htmlFor="dashboardAlerts">
                        <strong>Dashboard Alerts</strong>
                        <div className="text-muted" style={{ fontSize: '0.9em' }}>
                          Show notifications in dashboard
                        </div>
                      </label>
                    </div>
                  </div>

                  <div className="col-12">
                    <hr />
                  </div>

                  <div className="col-12">
                    <label className="form-label fw-bold">Notification Email</label>
                    <input
                      type="email"
                      className="form-control"
                      name="notification_email"
                      value={preferences.notification_email}
                      onChange={handlePreferenceChange}
                      placeholder="Enter email address for alerts"
                    />
                    <small className="text-muted">If empty, uses your primary email</small>
                  </div>

                  <div className="col-12">
                    <div className="alert alert-info">
                      <strong>Alert Types:</strong>
                      <ul className="mb-0 mt-2">
                        <li>Certificate expiration warnings</li>
                        <li>Failed certificate imports</li>
                        <li>System errors and maintenance</li>
                        <li>Security policy violations</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <button type="submit" className="btn btn-primary mt-4" disabled={loading}>
                  {loading ? 'Saving...' : '💾 Save Notification Settings'}
                </button>
              </form>
            </div>
          )}

          {/* Security Tab */}
          {activeTab === 'security' && (
            <div className="settings-card">
              <h4 className="mb-4">🛡️ Security Settings</h4>

              {/* Security Policies */}
              <form onSubmit={saveSecuritySettings}>
                <div className="security-section mb-4">
                  <h5 className="mb-3">🔐 Authentication & Access</h5>
                  
                  <div className="row g-3">
                    <div className="col-12">
                      <div className="form-check form-switch">
                        <input
                          className="form-check-input"
                          type="checkbox"
                          id="enable2fa"
                          name="enable_2fa"
                          checked={securitySettings.enable_2fa || false}
                          onChange={handleSecuritySettingsChange}
                        />
                        <label className="form-check-label" htmlFor="enable2fa">
                          <strong>Two-Factor Authentication (2FA)</strong>
                          <div className="text-muted" style={{ fontSize: '0.9em' }}>
                            Require 2FA for all logins
                          </div>
                        </label>
                      </div>
                    </div>

                    <div className="col-12">
                      <div className="form-check form-switch">
                        <input
                          className="form-check-input"
                          type="checkbox"
                          id="loginNotifications"
                          name="login_notifications"
                          checked={securitySettings.login_notifications !== false}
                          onChange={handleSecuritySettingsChange}
                        />
                        <label className="form-check-label" htmlFor="loginNotifications">
                          <strong>Login Notifications</strong>
                          <div className="text-muted" style={{ fontSize: '0.9em' }}>
                            Get alerts when someone logs into your account
                          </div>
                        </label>
                      </div>
                    </div>

                    <div className="col-12">
                      <div className="form-check form-switch">
                        <input
                          className="form-check-input"
                          type="checkbox"
                          id="suspiciousLoginAlerts"
                          name="suspicious_login_alerts"
                          checked={securitySettings.suspicious_login_alerts !== false}
                          onChange={handleSecuritySettingsChange}
                        />
                        <label className="form-check-label" htmlFor="suspiciousLoginAlerts">
                          <strong>Suspicious Login Alerts</strong>
                          <div className="text-muted" style={{ fontSize: '0.9em' }}>
                            Alert on logins from new locations or devices
                          </div>
                        </label>
                      </div>
                    </div>

                    <div className="col-12">
                      <div className="form-check form-switch">
                        <input
                          className="form-check-input"
                          type="checkbox"
                          id="ipWhitelist"
                          name="ip_whitelist_enabled"
                          checked={securitySettings.ip_whitelist_enabled || false}
                          onChange={handleSecuritySettingsChange}
                        />
                        <label className="form-check-label" htmlFor="ipWhitelist">
                          <strong>IP Whitelist</strong>
                          <div className="text-muted" style={{ fontSize: '0.9em' }}>
                            Only allow logins from approved IP addresses
                          </div>
                        </label>
                      </div>
                    </div>
                  </div>
                </div>

                <hr />

                {/* Session & Password Policy */}
                <div className="security-section mb-4">
                  <h5 className="mb-3">⏱️ Session & Password Policy</h5>
                  
                  <div className="row g-3">
                    <div className="col-md-6">
                      <label className="form-label fw-bold">Session Timeout (minutes)</label>
                      <input
                        type="number"
                        className="form-control"
                        name="session_timeout_minutes"
                        value={securitySettings.session_timeout_minutes || 30}
                        onChange={handleSecuritySettingsChange}
                        min="15"
                        max="480"
                      />
                      <small className="text-muted">Auto-logout after inactivity</small>
                    </div>

                    <div className="col-md-6">
                      <label className="form-label fw-bold">Password Expiry (days)</label>
                      <input
                        type="number"
                        className="form-control"
                        name="password_expiry_days"
                        value={securitySettings.password_expiry_days || 90}
                        onChange={handleSecuritySettingsChange}
                        min="30"
                        max="365"
                      />
                      <small className="text-muted">Require password change</small>
                    </div>

                    <div className="col-md-6">
                      <label className="form-label fw-bold">API Key Rotation (days)</label>
                      <input
                        type="number"
                        className="form-control"
                        name="api_key_rotation_days"
                        value={securitySettings.api_key_rotation_days || 90}
                        onChange={handleSecuritySettingsChange}
                        min="30"
                        max="365"
                      />
                      <small className="text-muted">Recommended: 90 days</small>
                    </div>
                  </div>
                </div>

                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Saving...' : '💾 Save Security Settings'}
                </button>
              </form>

              <hr className="my-4" />

              {/* API Keys Management */}
              <div className="security-section mb-4">
                <h5 className="mb-3">🔑 API Keys</h5>
                <p className="text-muted mb-3">
                  API keys allow external applications to access the CertEye API. Keep them secret!
                </p>

                <div className="table-responsive mb-3">
                  <table className="table table-sm">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Created</th>
                        <th>Last Used</th>
                        <th>Status</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {apiKeys.map(key => (
                        <tr key={key.id}>
                          <td className="fw-bold">{key.name}</td>
                          <td>{key.created}</td>
                          <td>{key.last_used}</td>
                          <td>
                            <span className={`badge ${key.status === 'active' ? 'bg-success' : 'bg-danger'}`}>
                              {key.status}
                            </span>
                          </td>
                          <td>
                            <button
                              type="button"
                              className="btn btn-outline-danger btn-sm"
                              onClick={() => revokeApiKey(key.id)}
                              disabled={loading}
                            >
                              Revoke
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <button
                  type="button"
                  className="btn btn-outline-primary btn-sm"
                  onClick={generateNewApiKey}
                  disabled={loading}
                >
                  ➕ Generate New API Key
                </button>

                <div className="alert alert-warning mt-3">
                  <strong>⚠️ Security Warning:</strong> Never share your API keys. If compromised, revoke immediately.
                </div>
              </div>

              <hr className="my-4" />

              {/* Active Sessions */}
              <div className="security-section mb-4">
                <h5 className="mb-3">👥 Active Sessions</h5>
                <div className="session-info mb-3">
                  <div className="d-flex justify-content-between align-items-center">
                    <div>
                      <strong>Current Session</strong>
                      <div className="text-muted">Browser: Chrome on Windows</div>
                      <div className="text-muted">IP: 192.168.1.100</div>
                      <div className="text-muted">Last activity: just now</div>
                    </div>
                    <span className="badge bg-success">Active</span>
                  </div>
                </div>
                <button type="button" className="btn btn-outline-danger btn-sm">
                  Sign Out All Other Sessions
                </button>
              </div>

              <hr className="my-4" />

              {/* Security Audit Log */}
              <div className="security-section">
                <h5 className="mb-3">📋 Security Audit Log</h5>
                <div className="table-responsive">
                  <table className="table table-sm">
                    <thead>
                      <tr>
                        <th>Event</th>
                        <th>Timestamp</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {securityLogs.map(log => (
                        <tr key={log.id}>
                          <td>{log.event}</td>
                          <td>{log.timestamp}</td>
                          <td>
                            <span className={`badge ${log.status === 'success' ? 'bg-success' : 'bg-danger'}`}>
                              {log.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <small className="text-muted">
                  Showing last 10 security events. <a href="#view-all">View all events →</a>
                </small>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default SettingsPage
