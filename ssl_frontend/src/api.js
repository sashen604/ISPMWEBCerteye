import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://localhost:8000'
})

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
  (error) => {
    if (error.response?.status === 401) {
      const requestUrl = error.config?.url || ''
      const isAgentIngestionEndpoint = requestUrl.includes('/api/certificates/collect_internal/')
      const hadAuthHeader = Boolean(error.config?.headers?.Authorization)

      if (isAgentIngestionEndpoint) {
        console.warn('[API] 401 from agent ingestion endpoint - preserving user auth tokens')
      } else if (hadAuthHeader) {
        console.warn('[API] 401 Unauthorized - Token may be invalid or expired')
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
      }
    }
    return Promise.reject(error)
  }
)

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
