import { useState, useEffect } from 'react'
import api from '../api'
import '../styles/admin-panel.css'

function AdminPanelPage() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedUser, setSelectedUser] = useState(null)
  const [newRole, setNewRole] = useState('')
  const [updating, setUpdating] = useState(false)
  const [filterRole, setFilterRole] = useState('all')

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      setLoading(true)
      setError('')
      console.log('[AdminPanel] Loading users...')
      const response = await api.get('/api/auth/users')
      setUsers(response.data.users || [])
    } catch (err) {
      console.error('[AdminPanel] Failed to load users:', err)
      setError(err.response?.data?.error || 'Failed to load users')
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
      console.log(`[AdminPanel] Updating user ${selectedUser.id} to role ${newRole}`)
      const response = await api.post(`/api/auth/users/${selectedUser.id}/role`, {
        role: newRole
      })
      
      // Update the user in the list
      setUsers(users.map(u => 
        u.id === selectedUser.id ? response.data.user : u
      ))
      
      setSelectedUser(response.data.user)
      setNewRole('')
      setError('')
    } catch (err) {
      console.error('[AdminPanel] Failed to update role:', err)
      setError(err.response?.data?.error || 'Failed to update role')
    } finally {
      setUpdating(false)
    }
  }

  const handleDeleteUser = async (userId, username) => {
    if (!window.confirm(`Are you sure you want to delete user "${username}"?`)) {
      return
    }

    try {
      console.log(`[AdminPanel] Deleting user ${userId}`)
      await api.delete(`/api/auth/users/${userId}/`)
      setUsers(users.filter(u => u.id !== userId))
      setSelectedUser(null)
      setError('')
    } catch (err) {
      console.error('[AdminPanel] Failed to delete user:', err)
      setError(err.response?.data?.error || 'Failed to delete user')
    }
  }

  const filteredUsers = filterRole === 'all' 
    ? users 
    : users.filter(u => u.role === filterRole)

  const getRoleColor = (role) => {
    const colors = {
      'superadmin': '#ffd60a',
      'admin': '#ff006e',
      'user': '#00f5ff',
      'viewer': '#9d4edd'
    }
    return colors[role] || '#9d4edd'
  }

  if (loading) {
    return (
      <div className="admin-panel-container">
        <div className="loading-spinner">Loading...</div>
      </div>
    )
  }

  return (
    <div className="admin-panel-container">
      <div className="admin-header">
        <h2>👨‍💼 Super Admin Panel</h2>
        <p>Manage users, roles, and permissions</p>
      </div>

      {error && (
        <div className="alert alert-danger">
          ❌ {error}
        </div>
      )}

      <div className="admin-content">
        {/* Users List */}
        <div className="users-section">
          <div className="section-header">
            <h3>Users ({filteredUsers.length})</h3>
            <div className="filter-controls">
              <select 
                className="form-control filter-select"
                value={filterRole}
                onChange={(e) => setFilterRole(e.target.value)}
              >
                <option value="all">All Roles</option>
                <option value="superadmin">Super Admin</option>
                <option value="admin">Admin</option>
                <option value="user">User</option>
                <option value="viewer">Viewer</option>
              </select>
              <button className="btn btn-refresh" onClick={loadUsers}>
                🔄 Refresh
              </button>
            </div>
          </div>

          <div className="users-list">
            {filteredUsers.length === 0 ? (
              <p className="no-users">No users found</p>
            ) : (
              filteredUsers.map(user => (
                <div 
                  key={user.id}
                  className={`user-item ${selectedUser?.id === user.id ? 'selected' : ''}`}
                  onClick={() => setSelectedUser(user)}
                >
                  <div className="user-info">
                    <h4>{user.username}</h4>
                    <p>{user.email}</p>
                  </div>
                  <div className="user-meta">
                    <span 
                      className="role-badge"
                      style={{ borderColor: getRoleColor(user.role) }}
                    >
                      {user.role_display}
                    </span>
                    <span className="active-badge">
                      {user.is_active ? '✅ Active' : '❌ Inactive'}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* User Detail */}
        {selectedUser && (
          <div className="user-detail-section">
            <div className="detail-header">
              <h3>User Details</h3>
              <button 
                className="btn btn-close"
                onClick={() => setSelectedUser(null)}
              >
                ✕
              </button>
            </div>

            <div className="detail-content">
              <div className="detail-field">
                <label>Username</label>
                <p>{selectedUser.username}</p>
              </div>

              <div className="detail-field">
                <label>Email</label>
                <p>{selectedUser.email}</p>
              </div>

              <div className="detail-field">
                <label>Current Role</label>
                <p style={{ color: getRoleColor(selectedUser.role) }}>
                  {selectedUser.role_display}
                </p>
              </div>

              <div className="detail-field">
                <label>Member Since</label>
                <p>{new Date(selectedUser.created_at).toLocaleDateString()}</p>
              </div>

              <div className="detail-field">
                <label>Status</label>
                <p>{selectedUser.is_active ? '✅ Active' : '❌ Inactive'}</p>
              </div>

              <div className="role-update-section">
                <h4>Update User Role</h4>
                <div className="role-selector">
                  <select 
                    className="form-control"
                    value={newRole}
                    onChange={(e) => setNewRole(e.target.value)}
                  >
                    <option value="">Select New Role</option>
                    <option value="superadmin">Super Admin</option>
                    <option value="admin">Admin</option>
                    <option value="user">User</option>
                    <option value="viewer">Viewer</option>
                  </select>
                  <button 
                    className="btn btn-primary"
                    onClick={handleRoleUpdate}
                    disabled={!newRole || updating}
                  >
                    {updating ? 'Updating...' : 'Update Role'}
                  </button>
                </div>
              </div>

              <div className="actions-section">
                <button 
                  className="btn btn-danger"
                  onClick={() => handleDeleteUser(selectedUser.id, selectedUser.username)}
                >
                  🗑️ Delete User
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="admin-stats">
        <div className="stat-card">
          <h4>Total Users</h4>
          <p className="stat-value">{users.length}</p>
        </div>
        <div className="stat-card">
          <h4>Super Admins</h4>
          <p className="stat-value">{users.filter(u => u.role === 'superadmin').length}</p>
        </div>
        <div className="stat-card">
          <h4>Admins</h4>
          <p className="stat-value">{users.filter(u => u.role === 'admin').length}</p>
        </div>
        <div className="stat-card">
          <h4>Regular Users</h4>
          <p className="stat-value">{users.filter(u => u.role === 'user').length}</p>
        </div>
      </div>
    </div>
  )
}

export default AdminPanelPage
