import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://localhost:8000'
})

let refreshInFlight = null

async function refreshAccessToken() {
  const refresh = localStorage.getItem('refresh_token')
  if (!refresh) {
    return null
  }
  const base = api.defaults.baseURL || ''
  try {
    const { data } = await axios.post(
      `${base}/api/auth/refresh`,
      { refresh },
      { headers: { 'Content-Type': 'application/json' } }
    )
    if (data.access) {
      localStorage.setItem('access_token', data.access)
    }
    if (data.refresh) {
      localStorage.setItem('refresh_token', data.refresh)
    }
    return data.access
  } catch (error) {
    // Token is invalid, expired, or blacklisted - clear tokens and return null
    console.warn('[API] Token refresh failed:', error.response?.data?.detail || error.message)
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    return null
  }
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  console.log(`[API] ${config.method?.toUpperCase()} ${config.url} - Token: ${token ? 'Present' : 'Missing'}`)
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error.response?.status
    const original = error.config
    const requestUrl = original?.url || ''

    if (status === 401 && original && !original._retry) {
      const isAuthCall =
        requestUrl.includes('/api/auth/login') ||
        requestUrl.includes('/api/auth/register') ||
        requestUrl.includes('/api/auth/refresh') ||
        requestUrl.includes('/api/auth/logout')
      const isAgentIngestionEndpoint = requestUrl.includes('/api/certificates/collect_internal/')
      const hadAuthHeader = Boolean(original.headers?.Authorization)

      if (isAgentIngestionEndpoint) {
        console.warn('[API] 401 from agent ingestion endpoint - preserving user auth tokens')
        return Promise.reject(error)
      }

      if (isAuthCall || !hadAuthHeader) {
        return Promise.reject(error)
      }

      original._retry = true
      try {
        if (!refreshInFlight) {
          refreshInFlight = refreshAccessToken().finally(() => {
            refreshInFlight = null
          })
        }
        const newAccess = await refreshInFlight
        if (!newAccess) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          return Promise.reject(error)
        }
        original.headers.Authorization = `Bearer ${newAccess}`
        return api(original)
      } catch (e) {
        console.warn('[API] Token refresh failed; logging out')
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        return Promise.reject(e)
      }
    }

    return Promise.reject(error)
  }
)

// Certificate Action API methods
export const certificateActionsApi = {
  // Acknowledge a certificate (internal_agent only)
  acknowledgeCertificate: async (certificateId) => {
    try {
      const response = await api.post(`/api/certificates/${certificateId}/acknowledge/`)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  // Rescan a certificate to recalculate metrics
  rescanCertificate: async (certificateId) => {
    try {
      const response = await api.post(`/api/certificates/${certificateId}/rescan/`)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  // Delete a certificate (admin only)
  deleteCertificate: async (certificateId) => {
    try {
      const response = await api.delete(`/api/certificates/${certificateId}/`)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  }
}

// Certificate Export API methods
export const exportApi = {
  // Export certificates with various filter options
  // filterType: 'all', 'expiring', 'high_risk', 'by_issuer', 'critical', 'custom'
  exportCertificates: async (filterType, params = {}) => {
    try {
      const queryParams = new URLSearchParams({
        filter_type: filterType,
        ...params
      })
      const response = await api.get(`/api/certificates/export_csv/?${queryParams}`, {
        responseType: 'blob'
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  }
}

// Alert API methods
export const alertApi = {
  // Get all alerts with optional filters
  getAlerts: async (filters = {}) => {
    try {
      const queryParams = new URLSearchParams(filters)
      const response = await api.get(`/api/alerts/?${queryParams}`)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  // Get alert statistics
  getAlertStats: async () => {
    try {
      const response = await api.get('/api/alerts/stats/')
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  // Generate alerts (admin-only)
  generateAlerts: async (alertTypes = ['EXPIRY', 'CRYPTO_WEAKNESS']) => {
    try {
      const response = await api.post('/api/alerts/generate/', {
        alert_types: alertTypes
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  }
}

export default api
