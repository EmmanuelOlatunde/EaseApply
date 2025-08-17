import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Axios instance
const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 10000, // shorter default
  headers: { 'Content-Type': 'application/json' }
})

// Token manager
export const tokenManager = {
  getAccessToken: () => localStorage.getItem('access_token'),
  setAccessToken: (t) => localStorage.setItem('access_token', t),
  getRefreshToken: () => localStorage.getItem('refresh_token'),
  setRefreshToken: (t) => localStorage.setItem('refresh_token', t),
  clearTokens: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }
}

// Request interceptor
api.interceptors.request.use((config) => {
  const token = tokenManager.getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Refresh handling with lock
let isRefreshing = false
let refreshSubscribers = []

function subscribeTokenRefresh(cb) { refreshSubscribers.push(cb) }
function onRefreshed(token) {
  refreshSubscribers.forEach(cb => cb(token))
  refreshSubscribers = []
}

// Response interceptor
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const originalRequest = err.config
    if (err.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise(resolve => {
          subscribeTokenRefresh(token => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(api(originalRequest))
          })
        })
      }

      originalRequest._retry = true
      isRefreshing = true
      try {
        const { data } = await api.post('/users/token/refresh/', {
          refresh: tokenManager.getRefreshToken()
        })
        tokenManager.setAccessToken(data.access)
        isRefreshing = false
        onRefreshed(data.access)
        originalRequest.headers.Authorization = `Bearer ${data.access}`
        return api(originalRequest)
      } catch (refreshErr) {
        isRefreshing = false
        tokenManager.clearTokens()
        window.location.href = '/login'
        return Promise.reject(refreshErr)
      }
    }
    return Promise.reject(err)
  }
)

export default api
