import api from '../api'

export async function register(username, email, password) {
  const response = await api.post('/api/auth/register', { username, email, password })
  return response.data
}

export async function login(username, password) {
  const response = await api.post('/api/auth/login', { username, password })
  const { access, refresh } = response.data
  localStorage.setItem('access_token', access)
  localStorage.setItem('refresh_token', refresh)
  return response.data
}

export function logout() {
  const refresh = localStorage.getItem('refresh_token')
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  return api.post('/api/auth/logout', { refresh })
}

export function getStoredUser() {
  return api.get('/api/auth/profile')
}

export function isAuthenticated() {
  return localStorage.getItem('access_token') !== null
}
