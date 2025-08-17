import axios from 'axios'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// Token management utilities
export const tokenManager = {
  getAccessToken: () => localStorage.getItem('authToken') || localStorage.getItem('access_token'),
  setAccessToken: (token) => {
    localStorage.setItem('authToken', token)
    localStorage.setItem('access_token', token)
  },
  getRefreshToken: () => localStorage.getItem('refresh_token'),
  setRefreshToken: (token) => localStorage.setItem('refresh_token', token),
  clearTokens: () => {
    localStorage.removeItem('authToken')
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }
}

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = tokenManager.getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      const refreshToken = tokenManager.getRefreshToken()
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/api/users/token/refresh/`, {
            refresh: refreshToken
          })
          
          const newAccessToken = response.data.access
          tokenManager.setAccessToken(newAccessToken)
          
          // Retry the original request with new token
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
          return api(originalRequest)
        } catch (refreshError) {
          // Refresh failed, clear tokens and redirect to login
          tokenManager.clearTokens()
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      } else {
        // No refresh token, clear tokens and redirect to login
        tokenManager.clearTokens()
        window.location.href = '/login'
      }
    }
    
    return Promise.reject(error)
  }
)

// Auth API calls
export const authAPI = {
  register: (userData) => api.post('/users/register/', userData),
  
  login: async (credentials) => {
    const response = await api.post('/users/login/', credentials)
    const { access, refresh, user } = response.data
    
    if (access) {
      tokenManager.setAccessToken(access)
    }
    if (refresh) {
      tokenManager.setRefreshToken(refresh)
    }
    
    return response
  },
  
  logout: async () => {
    try {
      await api.post('/users/logout/')
    } finally {
      tokenManager.clearTokens()
    }
  },
  
  changePassword: (passwordData) => api.put('/users/change-password/', passwordData),
  
  getProfile: () => api.get('/users/profile/'),
  
  updateProfile: (profileData) => api.put('/users/profile/', profileData),
  
  partialUpdateProfile: (profileData) => api.patch('/users/profile/', profileData),
  
  resendVerification: (email) => api.post('/users/resend-verification/', { email }),
  
  resetPassword: (email) => api.post('/users/password-reset-request/', { email }),
  
  resetPasswordConfirm: (resetData) => api.post('/reset-password-confirm/', resetData),
  
  verifyEmail: (uidb64, token) => api.get(`/users/email-verify/${uidb64}/${token}/`),
  
  refreshToken: (refreshToken) => api.post('/users/token/refresh/', { refresh: refreshToken })
}
 
// Jobs API calls
export const jobAPI = {
  list: (page = 1) => api.get(`/jobs/my-jobs/?page=${page}`),
  
  listAll: () => api.get('/jobs/'),
  
  create: (jobData) => api.post('/jobs/', jobData),
  
  get: (jobId) => api.get(`/jobs/${jobId}/`),
  
  update: (jobId, jobData) => api.put(`/jobs/${jobId}/`, jobData),
  
  delete: (jobId) => api.delete(`/jobs/${jobId}/`),
  
  reprocess: (jobId, jobData) => api.put(`/jobs/reprocess/${jobId}/`, jobData)
}

// Resume API calls
export const resumeAPI = {
  list: (page = 1) => api.get(`/resumes/?page=${page}`),
  
  upload: (formData) => {
    return api.post('/resumes/', formData, {
      headers: { 
        'Content-Type': 'multipart/form-data'
      },
      timeout: 60000 // Extended timeout for file uploads
    })
  },
  
  get: (resumeId) => api.get(`/resumes/${resumeId}/`),
  
  delete: (resumeId) => api.delete(`/resumes/${resumeId}/`),
  
  reparse: (resumeId) => api.put(`/resumes/${resumeId}/reparse/`),
  
  analytics: (page = 1) => api.get(`/resumes/analytics/?page=${page}`)
}

// Analysis API calls
export const analysisAPI = {
  generateCoverLetter: (data) => {
    return api.post('/analysis/generate-cover-letter/', data, {
      timeout: 60000, // Extended timeout for AI generation
      headers: {
        'Content-Type': 'application/json'
      }
    })
  },
  
  analyzeResume: (resumeId) => api.post(`/analysis/analyze-resume/${resumeId}/`),
  
  getMatchScore: (resumeId, jobId) => api.post('/analysis/match-score/', {
    resume_id: resumeId,
    job_id: jobId
  })
}

// Generic API error handler
export const handleAPIError = (error, defaultMessage = 'An error occurred') => {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response
    
    if (status === 400 && data.detail) {
      return data.detail
    }
    
    if (status === 401) {
      return 'Authentication failed. Please log in again.'
    }
    
    if (status === 403) {
      return 'Access denied. You do not have permission to perform this action.'
    }
    
    if (status === 404) {
      return 'Resource not found.'
    }
    
    if (status === 500) {
      return 'Server error. Please try again later.'
    }
    
    return data.detail || data.message || defaultMessage
  }
  
  if (error.request) {
    // Network error
    return 'Network error. Please check your internet connection.'
  }
  
  return error.message || defaultMessage
}

// Utility function to create FormData for file uploads
export const createFormData = (data) => {
  const formData = new FormData()
  
  Object.keys(data).forEach(key => {
    const value = data[key]
    if (value !== null && value !== undefined) {
      if (value instanceof File) {
        formData.append(key, value)
      } else if (Array.isArray(value)) {
        value.forEach(item => formData.append(key, item))
      } else {
        formData.append(key, value.toString())
      }
    }
  })
  
  return formData
}

// Export the configured axios instance as default
export default api
