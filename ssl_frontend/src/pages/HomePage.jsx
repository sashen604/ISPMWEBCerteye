import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { isAuthenticated } from '../services/auth'
import '../styles/home.css'

function HomePage() {
  const navigate = useNavigate()
  const [isAuth, setIsAuth] = useState(false)
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const checkAuth = async () => {
      const authenticated = isAuthenticated()
      setIsAuth(authenticated)
      
      if (authenticated) {
        try {
          const response = await fetch('/api/auth/profile', {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          })
          if (response.ok) {
            const data = await response.json()
            setUser(data.user)
          }
        } catch (err) {
          console.error('Failed to fetch profile:', err)
        }
      }
      setLoading(false)
    }

    checkAuth()
  }, [])

  if (loading) {
    return (
      <div className="home-loading">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    )
  }

  return (
    <div className="home-page">
      {/* Navigation */}
      <nav className="home-navbar">
        <div className="navbar-brand">
          <h1>🔐 CertEye</h1>
          <p>SSL/TLS Certificate Lifecycle Management</p>
        </div>
        <div className="navbar-actions">
          {isAuth ? (
            <>
              <span className="user-badge">
                👤 {user?.username} ({user?.role_display})
              </span>
              <button 
                className="btn btn-primary"
                onClick={() => navigate('/dashboard')}
              >
                Go to Dashboard
              </button>
            </>
          ) : (
            <>
              <button 
                className="btn btn-secondary"
                onClick={() => navigate('/login')}
              >
                Sign In
              </button>
              <button 
                className="btn btn-primary"
                onClick={() => navigate('/login')}
              >
                Get Started
              </button>
            </>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <h2>Monitor & Manage Your SSL/TLS Certificates</h2>
          <p>
            CertEye helps you track certificate expiration dates, assess security risks, 
            and ensure your HTTPS infrastructure stays secure and compliant.
          </p>
          <div className="hero-buttons">
            {!isAuth && (
              <>
                <button 
                  className="btn btn-lg btn-primary"
                  onClick={() => navigate('/login')}
                >
                  Start Monitoring Now
                </button>
                <button 
                  className="btn btn-lg btn-outline"
                  onClick={() => document.querySelector('#features').scrollIntoView({ behavior: 'smooth' })}
                >
                  Learn More
                </button>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="features-section">
        <h2>Why Choose CertEye?</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <h3>Real-time Monitoring</h3>
            <p>Monitor certificate expiration dates and get alerts before they expire</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🔍</div>
            <h3>Risk Assessment</h3>
            <p>Automatic risk scoring based on certificate health and expiration timeline</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🛡️</div>
            <h3>Security Analysis</h3>
            <p>Deep analysis of certificate chains and potential security issues</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📈</div>
            <h3>Performance Tracking</h3>
            <p>Track certificate performance metrics and historical data</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">👥</div>
            <h3>Role-Based Access</h3>
            <p>SuperAdmin, Admin, User, and Viewer roles for fine-grained control</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">⚙️</div>
            <h3>Easy Integration</h3>
            <p>Simple REST API for integrating certificate monitoring into your workflow</p>
          </div>
        </div>
      </section>

      {/* User Roles Section */}
      <section className="roles-section">
        <h2>User Roles & Permissions</h2>
        <div className="roles-grid">
          <div className="role-card superadmin">
            <h3>👨‍💼 Super Admin</h3>
            <p>Full system access and user management</p>
            <ul>
              <li>✅ Manage all users & roles</li>
              <li>✅ View all certificates</li>
              <li>✅ Access audit logs</li>
              <li>✅ System configuration</li>
              <li>✅ Create custom alerts</li>
            </ul>
          </div>

          <div className="role-card admin">
            <h3>👨‍💻 Admin</h3>
            <p>Manage certificates and team members</p>
            <ul>
              <li>✅ Scan & manage certificates</li>
              <li>✅ View team certificates</li>
              <li>✅ Create alerts</li>
              <li>✅ Generate reports</li>
              <li>❌ Cannot manage user roles</li>
            </ul>
          </div>

          <div className="role-card user">
            <h3>👨‍💼 User</h3>
            <p>Can scan and view certificates</p>
            <ul>
              <li>✅ Scan public domains</li>
              <li>✅ View own certificates</li>
              <li>✅ View basic statistics</li>
              <li>❌ Cannot create alerts</li>
              <li>❌ Cannot manage users</li>
            </ul>
          </div>

          <div className="role-card viewer">
            <h3>👁️ Viewer</h3>
            <p>Read-only access to certificates</p>
            <ul>
              <li>✅ View certificates</li>
              <li>✅ View reports</li>
              <li>✅ Export data</li>
              <li>❌ Cannot scan domains</li>
              <li>❌ Cannot create alerts</li>
            </ul>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="how-it-works">
        <h2>How CertEye Works</h2>
        <div className="steps-container">
          <div className="step">
            <div className="step-number">1</div>
            <h3>Register</h3>
            <p>Create your CertEye account and start as a User</p>
          </div>
          <div className="step-arrow">→</div>
          <div className="step">
            <div className="step-number">2</div>
            <h3>Scan Domains</h3>
            <p>Enter any domain to retrieve SSL certificate details</p>
          </div>
          <div className="step-arrow">→</div>
          <div className="step">
            <div className="step-number">3</div>
            <h3>Monitor</h3>
            <p>Track expiration dates and risk levels in real-time</p>
          </div>
          <div className="step-arrow">→</div>
          <div className="step">
            <div className="step-number">4</div>
            <h3>Upgrade Access</h3>
            <p>SuperAdmin can upgrade you to Admin for more features</p>
          </div>
        </div>
      </section>

      {/* Current User Status */}
      {isAuth && user && (
        <section className="user-status">
          <div className="status-card">
            <h3>Your Current Status</h3>
            <div className="status-info">
              <p><strong>Username:</strong> {user.username}</p>
              <p><strong>Email:</strong> {user.email}</p>
              <p><strong>Role:</strong> <span className={`role-badge ${user.role}`}>{user.role_display}</span></p>
              <p><strong>Member Since:</strong> {new Date(user.created_at).toLocaleDateString()}</p>
            </div>
            <div className="status-actions">
              {user.role === 'user' && (
                <p className="info-text">💡 SuperAdmins can upgrade your role to Admin for more features!</p>
              )}
              <button 
                className="btn btn-primary"
                onClick={() => navigate('/dashboard')}
              >
                Go to Dashboard →
              </button>
            </div>
          </div>
        </section>
      )}

      {/* Footer */}
      <footer className="home-footer">
        <div className="footer-content">
          <p>© 2026 CertEye - SSL/TLS Certificate Lifecycle Management</p>
          <p>Keeping your HTTPS infrastructure secure and compliant</p>
        </div>
      </footer>
    </div>
  )
}

export default HomePage
