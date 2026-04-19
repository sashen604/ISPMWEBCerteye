import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login, register } from '../services/auth'
import '../styles/auth.css'

function LoginPage() {
  const navigate = useNavigate()
  const [isLogin, setIsLogin] = useState(true)
  const [form, setForm] = useState({ 
    username: '', 
    email: '',
    password: '', 
    confirmPassword: ''
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (isLogin) {
        await login(form.username, form.password)
      } else {
        if (form.password !== form.confirmPassword) {
          setError('Passwords do not match')
          setLoading(false)
          return
        }
        await register(form.username, form.email, form.password)
        // Auto-login after registration
        await login(form.username, form.password)
      }
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.message || `${isLogin ? 'Login' : 'Registration'} failed`)
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setForm({ username: '', email: '', password: '', confirmPassword: '' })
    setError('')
  }

  const handleToggle = () => {
    setIsLogin(!isLogin)
    handleReset()
  }

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <h1 className="auth-title">🔐 CertEye</h1>
            <p className="auth-subtitle">SSL/TLS Certificate Management</p>
          </div>

          <div className="auth-tabs">
            <button 
              className={`auth-tab ${isLogin ? 'active' : ''}`}
              onClick={() => handleToggle()}
            >
              Sign In
            </button>
            <button 
              className={`auth-tab ${!isLogin ? 'active' : ''}`}
              onClick={() => handleToggle()}
            >
              Sign Up
            </button>
          </div>

          {error && (
            <div className="alert alert-danger py-2 mb-3">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {!isLogin && (
              <div className="mb-3">
                <label className="form-label">Email</label>
                <input
                  type="email"
                  className="form-control"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  placeholder="you@example.com"
                  required
                />
              </div>
            )}

            <div className="mb-3">
              <label className="form-label">Username</label>
              <input
                type="text"
                className="form-control"
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                placeholder={isLogin ? 'admin' : 'username'}
                required
              />
            </div>

            <div className="mb-3">
              <label className="form-label">Password</label>
              <input
                type="password"
                className="form-control"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder="••••••••"
                required
              />
            </div>

            {!isLogin && (
              <div className="mb-3">
                <label className="form-label">Confirm Password</label>
                <input
                  type="password"
                  className="form-control"
                  value={form.confirmPassword}
                  onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
                  placeholder="••••••••"
                  required
                />
              </div>
            )}

            <button type="submit" className="btn btn-primary w-100 auth-btn" disabled={loading}>
              {loading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2"></span>
                  {isLogin ? 'Signing in...' : 'Creating account...'}
                </>
              ) : (
                isLogin ? 'Sign In' : 'Create Account'
              )}
            </button>
          </form>

          <p className="auth-footer">
            {isLogin ? "Don't have an account? " : 'Already have an account? '}
            <button 
              type="button"
              className="auth-link"
              onClick={handleToggle}
            >
              {isLogin ? 'Sign up' : 'Sign in'}
            </button>
          </p>
        </div>

        <div className="auth-footer-info">
          <p>🔒 Your credentials are secure and encrypted</p>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
