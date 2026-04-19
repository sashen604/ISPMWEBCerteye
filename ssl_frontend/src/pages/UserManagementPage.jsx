import { useState, useEffect } from 'react'
import api from '../api'
import '../styles/user-management.css'

function UserManagementPage() {
  const [activeTab, setActiveTab] = useState('users')
  const [users, setUsers] = useState([])
  const [loginLogs, setLoginLogs] = useState([])
  const [registrationLogs, setRegistrationLogs] = useState([])
  const [auditLogs, setAuditLogs] = useState([])
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  
  const [selectedUser, setSelectedUser] = useState(null)
  const [newRole, setNewRole] = useState('')
  const [updating, setUpdating] = useState(false)
  const [deleting, setDeleting] = useState(false)
  
  const [filterRole, setFilterRole] = useState('all')
  const [filterStatus, setFilterStatus] = useState('all')
  const [searchUser, setSearchUser] = useState('')

  useEffect(() => {
    if (activeTab === 'users') {
      loadUsers()
    } else if (activeTab === 'login-logs') {
      loadLoginLogs()
    } else if (activeTab === 'registration-logs') {
      loadRegistrationLogs()
    } else if (activeTab === 'audit-logs') {
      loadAuditLogs()
    }
  }, [activeTab])

  const loadUsers = async () => {
    try {
      setLoading(true)
      setError('')
      const response = await api.get('/api/auth/users')
      setUsers(response.data.users || [])
    } catch (err) {
      console.error('Failed to load users:', err)
      setError(err.response?.data?.error || 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  const loadLoginLogs = async () => {
    try {
      setLoading(true)
      setError('')
      const response = await api.get('/api/auth/logs/login')
      setLoginLogs(response.data.logs || [])
    } catch (err) {
      console.error('Failed to load login logs:', err)
      setError(err.response?.data?.error || 'Failed to load login logs')
    } finally {
      setLoading(false)
    }
  }

  const loadRegistrationLogs = async () => {
    try {
      setLoading(true)
      setError('')
      const response = await api.get('/api/auth/logs/registration')
      setRegistrationLogs(response.data.logs || [])
    } catch (err) {
      console.error('Failed to load registration logs:', err)
      setError(err.response?.data?.error || 'Failed to load registration logs')
    } finally {
      setLoading(false)
    }
  }

  const loadAuditLogs = async () => {
    try {
      setLoading(true)
      setError('')
      const response = await api.get('/api/auth/logs/audit')
      setAuditLogs(response.data.logs || [])
    } catch (err) {
      console.error('Failed to load audit logs:', err)
      setError(err.response?.data?.error || 'Failed to load audit logs')
    } finally {
      setLoading(false)
    }
  }

  const handleRoleUpdate = async () => {
    if (!selectedUser || !newRole) {
      setError('Please select a user and role')
      return
    }

    setUpdating(true)
    try {
      const response = await api.post(`/api/auth/users/${selectedUser.id}/role`, {
        role: newRole
      })
      
      setUsers(users.map(u => 
        u.id === selectedUser.id ? response.data.user : u
      ))
      
      setSelectedUser(response.data.user)
      setNewRole('')
      setError('')
      setMessage(`✅ Role updated successfully for ${selectedUser.username}`)
      setTimeout(() => setMessage(''), 3000)
    } catch (err) {
      console.error('Failed to update role:', err)
      setError(err.response?.data?.error || 'Failed to update role')
    } finally {
      setUpdating(false)
    }
  }

  const handleDeleteUser = async (userId, username) => {
    if (!window.confirm(`Are you sure you want to delete user "${username}"? This action cannot be undone.`)) {
      return
    }

    setDeleting(true)
    try {
      await api.delete(`/api/auth/users/${userId}/`)
      setUsers(users.filter(u => u.id !== userId))
      setSelectedUser(null)
      setError('')
      setMessage(`✅ User ${username} deleted successfully`)
      setTimeout(() => setMessage(''), 3000)
    } catch (err) {
      console.error('Failed to delete user:', err)
      setError(err.response?.data?.error || 'Failed to delete user')
    } finally {
      setDeleting(false)
    }
  }

  const handleStatusToggle = async (user) => {
    setUpdating(true)
    try {
      const response = await api.patch(`/api/auth/users/${user.id}/`, {
        is_active: !user.is_active
      })
      
      setUsers(users.map(u => 
        u.id === user.id ? { ...u, is_active: !u.is_active } : u
      ))
      
      if (selectedUser?.id === user.id) {
        setSelectedUser({ ...selectedUser, is_active: !selectedUser.is_active })
      }
      
      setMessage(`✅ User status updated to ${!user.is_active ? 'Active' : 'Inactive'}`)
      setTimeout(() => setMessage(''), 3000)
    } catch (err) {
      console.error('Failed to update user status:', err)
      setError(err.response?.data?.error || 'Failed to update status')
    } finally {
      setUpdating(false)
    }
  }

  const getRoleColor = (role) => {
    const colors = {
      'superadmin': '#ffd60a',
      'admin': '#ff006e',
      'user': '#00f5ff',
      'viewer': '#9d4edd'
    }
    return colors[role] || '#9d4edd'
  }

  const getRoleEmoji = (role) => {
    const emojis = {
      'superadmin': '👑',
      'admin': '🛡️',
      'user': '👤',
      'viewer': '👁️'
    }
    return emojis[role] || '❓'
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString()
  }

  const getStatusEmoji = (isActive) => {
    return isActive ? '✅' : '🔒'
  }

  const getLoginStatusColor = (isSuccessful) => {
    return isSuccessful ? '#28a745' : '#dc3545'
  }

  const filteredUsers = users.filter(u => {
    const matchesRole = filterRole === 'all' || u.role === filterRole
    const matchesStatus = filterStatus === 'all' || (filterStatus === 'active' ? u.is_active : !u.is_active)
    const matchesSearch = searchUser === '' || u.username.toLowerCase().includes(searchUser.toLowerCase()) || u.email.toLowerCase().includes(searchUser.toLowerCase())
    return matchesRole && matchesStatus && matchesSearch
  })

  if (loading) {
    return (
      <div className="user-management-container">
        <div className="loading-spinner">🔄 Loading...</div>
      </div>
    )
  }

  return (
    <div className="user-management-container">
      <div className="um-header">
        <h1>👥 User Management Center</h1>
        <p>Manage users, roles, permissions, and view system audit logs</p>
      </div>

      {error && <div className="alert alert-danger alert-dismissible">
        <strong>⚠️ Error:</strong> {error}
        <button className="btn-close" onClick={() => setError('')}></button>
      </div>}

      {message && <div className="alert alert-success alert-dismissible">
        {message}
        <button className="btn-close" onClick={() => setMessage('')}></button>
      </div>}

      <div className="um-tabs">
        <button 
          className={`um-tab ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          👥 Users ({users.length})
        </button>
        <button 
          className={`um-tab ${activeTab === 'registration-logs' ? 'active' : ''}`}
          onClick={() => setActiveTab('registration-logs')}
        >
          📝 Registrations ({registrationLogs.length})
        </button>
        <button 
          className={`um-tab ${activeTab === 'login-logs' ? 'active' : ''}`}
          onClick={() => setActiveTab('login-logs')}
        >
          🔑 Login Logs ({loginLogs.length})
        </button>
        <button 
          className={`um-tab ${activeTab === 'audit-logs' ? 'active' : ''}`}
          onClick={() => setActiveTab('audit-logs')}
        >
          📋 Audit Logs ({auditLogs.length})
        </button>
      </div>

      <div className="um-content">
        {/* Users Tab */}
        {activeTab === 'users' && (
          <div className="um-section">
            <div className="um-filters">
              <input 
                type="text" 
                placeholder="🔍 Search by username or email..."
                value={searchUser}
                onChange={(e) => setSearchUser(e.target.value)}
                className="form-control search-input"
              />
              <select 
                value={filterRole}
                onChange={(e) => setFilterRole(e.target.value)}
                className="form-control filter-select"
              >
                <option value="all">🔹 All Roles</option>
                <option value="superadmin">👑 SuperAdmin</option>
                <option value="admin">🛡️ Admin</option>
                <option value="user">👤 User</option>
                <option value="viewer">👁️ Viewer</option>
              </select>
              <select 
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="form-control filter-select"
              >
                <option value="all">📊 All Status</option>
                <option value="active">✅ Active</option>
                <option value="inactive">🔒 Inactive</option>
              </select>
            </div>

            <div className="um-users-grid">
              <div className="um-users-list">
                <h3>Users List ({filteredUsers.length})</h3>
                <div className="users-scroll">
                  {filteredUsers.length === 0 ? (
                    <p className="text-muted text-center py-5">No users found matching your filters</p>
                  ) : (
                    filteredUsers.map(user => (
                      <div 
                        key={user.id}
                        className={`user-card ${selectedUser?.id === user.id ? 'selected' : ''}`}
                        onClick={() => {
                          setSelectedUser(user)
                          setNewRole(user.role)
                        }}
                      >
                        <div className="user-card-header">
                          <div className="user-info">
                            <h5>{user.username}</h5>
                            <small>{user.email}</small>
                          </div>
                          <span 
                            className="role-badge"
                            style={{ backgroundColor: getRoleColor(user.role) }}
                          >
                            {getRoleEmoji(user.role)} {user.role_display}
                          </span>
                        </div>
                        <div className="user-card-footer">
                          <span className="status-badge">
                            {getStatusEmoji(user.is_active)} {user.is_active ? 'Active' : 'Inactive'}
                          </span>
                          <small>Joined: {formatDate(user.created_at)}</small>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {selectedUser && (
                <div className="um-user-detail">
                  <h3>📋 User Details</h3>
                  <div className="detail-card">
                    <div className="detail-row">
                      <label>Username:</label>
                      <span>{selectedUser.username}</span>
                    </div>
                    <div className="detail-row">
                      <label>Email:</label>
                      <span>{selectedUser.email}</span>
                    </div>
                    <div className="detail-row">
                      <label>Current Role:</label>
                      <span style={{ color: getRoleColor(selectedUser.role), fontWeight: 'bold' }}>
                        {getRoleEmoji(selectedUser.role)} {selectedUser.role_display}
                      </span>
                    </div>
                    <div className="detail-row">
                      <label>Status:</label>
                      <span>{getStatusEmoji(selectedUser.is_active)} {selectedUser.is_active ? 'Active' : 'Inactive'}</span>
                    </div>
                    <div className="detail-row">
                      <label>Member Since:</label>
                      <span>{formatDate(selectedUser.created_at)}</span>
                    </div>

                    <div className="um-actions">
                      <div className="role-selector">
                        <label>Change Role:</label>
                        <select 
                          value={newRole}
                          onChange={(e) => setNewRole(e.target.value)}
                          className="form-control"
                        >
                          <option value="superadmin">👑 SuperAdmin</option>
                          <option value="admin">🛡️ Admin</option>
                          <option value="user">👤 User</option>
                          <option value="viewer">👁️ Viewer</option>
                        </select>
                        <button 
                          className="btn btn-primary btn-sm"
                          onClick={handleRoleUpdate}
                          disabled={updating || newRole === selectedUser.role}
                        >
                          {updating ? '⏳ Updating...' : '💾 Update Role'}
                        </button>
                      </div>

                      <div className="status-actions">
                        <button 
                          className={`btn btn-sm ${selectedUser.is_active ? 'btn-warning' : 'btn-success'}`}
                          onClick={() => handleStatusToggle(selectedUser)}
                          disabled={updating}
                        >
                          {selectedUser.is_active ? '🔒 Deactivate' : '✅ Activate'}
                        </button>
                      </div>

                      {selectedUser.id !== parseInt(localStorage.getItem('userId') || '0') && (
                        <button 
                          className="btn btn-danger btn-sm"
                          onClick={() => handleDeleteUser(selectedUser.id, selectedUser.username)}
                          disabled={deleting}
                        >
                          {deleting ? '⏳ Deleting...' : '🗑️ Delete User'}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Registration Logs Tab */}
        {activeTab === 'registration-logs' && (
          <div className="um-section">
            <h3>📝 User Registration Logs ({registrationLogs.length})</h3>
            {registrationLogs.length === 0 ? (
              <p className="text-muted text-center py-5">No registration logs found</p>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover">
                  <thead>
                    <tr>
                      <th>Username</th>
                      <th>Email</th>
                      <th>Initial Role</th>
                      <th>Registered By</th>
                      <th>Registration Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {registrationLogs.map(log => (
                      <tr key={log.id}>
                        <td><strong>{log.username}</strong></td>
                        <td>{log.email}</td>
                        <td>
                          <span 
                            className="badge"
                            style={{ backgroundColor: getRoleColor(log.initial_role) }}
                          >
                            {log.initial_role}
                          </span>
                        </td>
                        <td>{log.registered_by_username || 'Self-registered'}</td>
                        <td>{formatDate(log.registration_time)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Login Logs Tab */}
        {activeTab === 'login-logs' && (
          <div className="um-section">
            <h3>🔑 Login Activity Logs ({loginLogs.length})</h3>
            {loginLogs.length === 0 ? (
              <p className="text-muted text-center py-5">No login logs found</p>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover">
                  <thead>
                    <tr>
                      <th>Username</th>
                      <th>Status</th>
                      <th>Login Time</th>
                      <th>Logout Time</th>
                      <th>Duration</th>
                      <th>IP Address</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loginLogs.map(log => (
                      <tr key={log.id}>
                        <td><strong>{log.username}</strong></td>
                        <td>
                          <span 
                            className="badge"
                            style={{ backgroundColor: getLoginStatusColor(log.is_successful) }}
                          >
                            {log.is_successful ? '✅ Success' : `❌ Failed: ${log.failure_reason}`}
                          </span>
                        </td>
                        <td>{formatDate(log.login_time)}</td>
                        <td>{log.logout_time ? formatDate(log.logout_time) : '⏳ Active'}</td>
                        <td>{log.session_duration ? `${Math.floor(log.session_duration / 60)}m ${log.session_duration % 60}s` : '-'}</td>
                        <td><code>{log.ip_address || 'N/A'}</code></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Audit Logs Tab */}
        {activeTab === 'audit-logs' && (
          <div className="um-section">
            <h3>📋 Administrative Audit Logs ({auditLogs.length})</h3>
            {auditLogs.length === 0 ? (
              <p className="text-muted text-center py-5">No audit logs found</p>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover">
                  <thead>
                    <tr>
                      <th>Action</th>
                      <th>Performed By</th>
                      <th>Target User</th>
                      <th>Old Value</th>
                      <th>New Value</th>
                      <th>IP Address</th>
                      <th>Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditLogs.map(log => (
                      <tr key={log.id}>
                        <td><strong>{log.action_display}</strong></td>
                        <td>{log.actor_username || 'System'}</td>
                        <td>{log.target_username}</td>
                        <td><code>{JSON.stringify(log.old_value)}</code></td>
                        <td><code>{JSON.stringify(log.new_value)}</code></td>
                        <td><code>{log.ip_address || 'N/A'}</code></td>
                        <td>{formatDate(log.timestamp)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default UserManagementPage