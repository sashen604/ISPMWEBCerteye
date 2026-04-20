import React, { useState, useEffect } from 'react';
import api from '../api';
import '../styles/adcs.css';

const ADCSSourceForm = () => {
  const [formData, setFormData] = useState({
    source_name: '',
    description: '',
    server_hostname: '',
    server_ip: '',
    ca_name: '',
    domain: '',
    username: '',
    password: '',
    auth_type: 'winrm',
    port: 5986,
    use_ssl: true,
    verify_ssl: true,
    auto_sync_enabled: true,
    sync_interval_hours: 24,
    is_active: true,
  });

  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [testResults, setTestResults] = useState(null);
  const [syncResults, setSyncResults] = useState(null);
  const [selectedSource, setSelectedSource] = useState(null);
  const [syncHistory, setSyncHistory] = useState([]);

  // Load existing AD CS sources
  useEffect(() => {
    loadSources();
  }, []);

  const loadSources = async () => {
    try {
      const response = await api.get('/api/certificates/adcs-sources/');
      setSources(response.data.results || response.data);
    } catch (error) {
      console.error('Failed to load sources:', error);
    }
  };

  const loadSyncHistory = async (sourceId) => {
    try {
      const response = await api.get(
        `/api/certificates/adcs-sources/${sourceId}/sync_history/?limit=10`
      );
      setSyncHistory(response.data.results || []);
    } catch (error) {
      console.error('Failed to load sync history:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const response = await api.post('/api/certificates/adcs-sources/', formData);
      setMessage({
        type: 'success',
        text: `AD CS source "${response.data.source_name}" registered successfully!`,
      });
      setFormData({
        source_name: '',
        description: '',
        server_hostname: '',
        server_ip: '',
        ca_name: '',
        domain: '',
        username: '',
        password: '',
        auth_type: 'winrm',
        port: 5986,
        use_ssl: true,
        verify_ssl: true,
        auto_sync_enabled: true,
        sync_interval_hours: 24,
        is_active: true,
      });
      loadSources();
    } catch (error) {
      setMessage({
        type: 'error',
        text: `Failed to register AD CS source: ${error.response?.data?.detail || error.message}`,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async (sourceId) => {
    setLoading(true);
    setTestResults(null);

    try {
      const response = await api.post(
        `/api/certificates/adcs-sources/${sourceId}/test_connection/`
      );
      setTestResults(response.data);
      setMessage({
        type: response.data.success ? 'success' : 'error',
        text: response.data.message,
      });
    } catch (error) {
      setTestResults({
        success: false,
        message: error.response?.data?.detail || error.message,
      });
      setMessage({
        type: 'error',
        text: 'Connection test failed',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async (sourceId) => {
    setLoading(true);
    setSyncResults(null);

    try {
      const response = await api.post(
        `/api/certificates/adcs-sources/${sourceId}/sync/`
      );
      setSyncResults(response.data);
      setMessage({
        type: response.data.success ? 'success' : 'error',
        text: response.data.message,
      });
      loadSources();
      loadSyncHistory(sourceId);
    } catch (error) {
      setSyncResults({
        success: false,
        message: error.response?.data?.detail || error.message,
      });
      setMessage({
        type: 'error',
        text: 'Sync failed',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSource = async (source) => {
    const confirmed = window.confirm(
      `Remove AD CS source "${source.source_name}"? This cannot be undone.`
    );
    if (!confirmed) {
      return;
    }

    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      await api.delete(`/api/certificates/adcs-sources/${source.id}/`);

      if (selectedSource?.id === source.id) {
        setSelectedSource(null);
        setSyncHistory([]);
        setTestResults(null);
        setSyncResults(null);
      }

      setMessage({
        type: 'success',
        text: `AD CS source "${source.source_name}" removed successfully.`,
      });
      loadSources();
    } catch (error) {
      setMessage({
        type: 'error',
        text: `Failed to remove AD CS source: ${error.response?.data?.detail || error.message}`,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSourceClick = (source) => {
    setSelectedSource(source);
    loadSyncHistory(source.id);
    setTestResults(null);
    setSyncResults(null);
  };

  return (
    <div className="adcs-container">
      <h1>Active Directory Certificate Services (AD CS) Management</h1>

      {message.text && (
        <div className={`message message-${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="adcs-layout">
        {/* Registration Form */}
        <div className="adcs-form-section">
          <h2>Register New AD CS Source</h2>
          <form onSubmit={handleSubmit} className="adcs-form">
            <div className="form-group">
              <label htmlFor="source_name">Source Name*</label>
              <input
                type="text"
                id="source_name"
                name="source_name"
                value={formData.source_name}
                onChange={handleInputChange}
                placeholder="e.g., Production-CA"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="description">Description</label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                placeholder="Optional description"
                rows="3"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="server_hostname">Server Hostname*</label>
                <input
                  type="text"
                  id="server_hostname"
                  name="server_hostname"
                  value={formData.server_hostname}
                  onChange={handleInputChange}
                  placeholder="ca.example.com"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="server_ip">Server IP*</label>
                <input
                  type="text"
                  id="server_ip"
                  name="server_ip"
                  value={formData.server_ip}
                  onChange={handleInputChange}
                  placeholder="192.168.1.100"
                  required
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="ca_name">CA Name*</label>
                <input
                  type="text"
                  id="ca_name"
                  name="ca_name"
                  value={formData.ca_name}
                  onChange={handleInputChange}
                  placeholder="Example-CA"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="domain">Domain*</label>
                <input
                  type="text"
                  id="domain"
                  name="domain"
                  value={formData.domain}
                  onChange={handleInputChange}
                  placeholder="example.com"
                  required
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="auth_type">Authentication Method*</label>
                <select
                  id="auth_type"
                  name="auth_type"
                  value={formData.auth_type}
                  onChange={handleInputChange}
                  required
                >
                  <option value="winrm">WinRM PowerShell</option>
                  <option value="ldap">LDAP Query</option>
                  <option value="agent">Local Agent</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="port">Port</label>
                <input
                  type="number"
                  id="port"
                  name="port"
                  value={formData.port}
                  onChange={handleInputChange}
                  min="1"
                  max="65535"
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="username">Username*</label>
                <input
                  type="text"
                  id="username"
                  name="username"
                  value={formData.username}
                  onChange={handleInputChange}
                  placeholder="domain\\username"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="password">Password*</label>
                <input
                  type="password"
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  placeholder="Service account password"
                  required
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group checkbox">
                <label htmlFor="use_ssl">
                  <input
                    type="checkbox"
                    id="use_ssl"
                    name="use_ssl"
                    checked={formData.use_ssl}
                    onChange={handleInputChange}
                  />
                  Use SSL/HTTPS
                </label>
              </div>

              <div className="form-group checkbox">
                <label htmlFor="verify_ssl">
                  <input
                    type="checkbox"
                    id="verify_ssl"
                    name="verify_ssl"
                    checked={formData.verify_ssl}
                    onChange={handleInputChange}
                  />
                  Verify SSL Certificate
                </label>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group checkbox">
                <label htmlFor="auto_sync_enabled">
                  <input
                    type="checkbox"
                    id="auto_sync_enabled"
                    name="auto_sync_enabled"
                    checked={formData.auto_sync_enabled}
                    onChange={handleInputChange}
                  />
                  Enable Automatic Sync
                </label>
              </div>

              <div className="form-group">
                <label htmlFor="sync_interval_hours">Sync Interval (hours)</label>
                <input
                  type="number"
                  id="sync_interval_hours"
                  name="sync_interval_hours"
                  value={formData.sync_interval_hours}
                  onChange={handleInputChange}
                  min="1"
                  max="720"
                />
              </div>
            </div>

            <div className="form-group checkbox">
              <label htmlFor="is_active">
                <input
                  type="checkbox"
                  id="is_active"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleInputChange}
                />
                Active
              </label>
            </div>

            <button type="submit" disabled={loading} className="btn btn-primary">
              {loading ? 'Registering...' : 'Register AD CS Source'}
            </button>
          </form>
        </div>

        {/* Sources List */}
        <div className="adcs-sources-section">
          <h2>Registered AD CS Sources</h2>
          {sources.length === 0 ? (
            <p className="no-data">No AD CS sources registered yet</p>
          ) : (
            <div className="sources-list">
              {sources.map((source) => (
                <div
                  key={source.id}
                  className={`source-card ${selectedSource?.id === source.id ? 'active' : ''}`}
                  onClick={() => handleSourceClick(source)}
                >
                  <div className="source-header">
                    <h3>{source.source_name}</h3>
                    <span className={`status-badge status-${source.connection_status}`}>
                      {source.connection_status_display}
                    </span>
                  </div>

                  <div className="source-info">
                    <p>
                      <strong>CA Name:</strong> {source.ca_name}
                    </p>
                    <p>
                      <strong>Server:</strong> {source.server_hostname}
                    </p>
                    <p>
                      <strong>Auth Type:</strong> {source.auth_type_display}
                    </p>
                    <p>
                      <strong>Certificates:</strong> {source.certificate_count}
                    </p>
                    {source.last_sync_at && (
                      <p>
                        <strong>Last Sync:</strong>{' '}
                        {new Date(source.last_sync_at).toLocaleString()}
                      </p>
                    )}
                  </div>

                  <div className="source-actions">
                    <button
                      className="btn btn-sm btn-info"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleTestConnection(source.id);
                      }}
                      disabled={loading}
                    >
                      Test Connection
                    </button>
                    <button
                      className="btn btn-sm btn-success"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSync(source.id);
                      }}
                      disabled={loading}
                    >
                      Sync Now
                    </button>
                    <button
                      className="btn btn-sm btn-danger"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteSource(source);
                      }}
                      disabled={loading}
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Details Section */}
      {selectedSource && (
        <div className="adcs-details-section">
          <h2>
            Details: {selectedSource.source_name}
            <button
              className="btn btn-sm"
              onClick={() => {
                setSelectedSource(null);
                setSyncHistory([]);
              }}
            >
              Close
            </button>
          </h2>

          {/* Test Results */}
          {testResults && (
            <div className={`results-box results-${testResults.success ? 'success' : 'error'}`}>
              <h3>Connection Test Results</h3>
              <p>{testResults.message}</p>
              {testResults.timestamp && (
                <p className="small">
                  Tested: {new Date(testResults.timestamp).toLocaleString()}
                </p>
              )}
            </div>
          )}

          {/* Sync Results */}
          {syncResults && (
            <div className={`results-box results-${syncResults.success ? 'success' : 'error'}`}>
              <h3>Sync Results</h3>
              <p>{syncResults.message}</p>
              {syncResults.stats && (
                <div className="sync-stats">
                  <p>
                    <strong>Fetched:</strong> {syncResults.stats.certificates_fetched}
                  </p>
                  <p>
                    <strong>Imported:</strong> {syncResults.stats.certificates_imported}
                  </p>
                  <p>
                    <strong>Updated:</strong> {syncResults.stats.certificates_updated}
                  </p>
                  <p>
                    <strong>Failed:</strong> {syncResults.stats.certificates_failed}
                  </p>
                  {syncResults.duration_seconds && (
                    <p>
                      <strong>Duration:</strong> {syncResults.duration_seconds}s
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Sync History */}
          <div className="sync-history">
            <h3>Sync History</h3>
            {syncHistory.length === 0 ? (
              <p className="no-data">No sync history available</p>
            ) : (
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Status</th>
                    <th>Type</th>
                    <th>Imported</th>
                    <th>Failed</th>
                    <th>Duration</th>
                    <th>Completed</th>
                  </tr>
                </thead>
                <tbody>
                  {syncHistory.map((history) => (
                    <tr key={history.id}>
                      <td>
                        <span className={`status-badge status-${history.status}`}>
                          {history.status_display}
                        </span>
                      </td>
                      <td>{history.sync_type}</td>
                      <td>{history.certificates_imported}</td>
                      <td>{history.certificates_failed}</td>
                      <td>{history.duration_seconds}s</td>
                      <td>
                        {history.completed_at
                          ? new Date(history.completed_at).toLocaleString()
                          : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ADCSSourceForm;
