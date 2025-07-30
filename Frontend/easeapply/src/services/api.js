import axios from 'axios'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// Request interceptor to add auth token if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized - redirect to login
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      // You might want to redirect to login page here
    }
    return Promise.reject(error)
  }
)

// Auth API calls
export const authAPI = {
  register: (userData) => api.post('/users/register/', userData),
  login: (credentials) => api.post('/users/login/', credentials),
  logout: () => api.post('/users/logout/'),
  changePassword: (passwordData) => api.put('/users/change-password/', passwordData),
  updateProfile: (profileData) => api.put('/users/profile/', profileData),
  resendVerification: (email) => api.post('/users/resend-verification/', { email }),
  resetPasswordConfirm: (resetData) => api.post('/users/reset-password-confirm/', resetData),
  verifyEmail: (uidb64, token) => api.get(`/users/email-verify/${uidb64}/${token}/`)
}

// Analysis API calls
export const analysisAPI = {
  generateCoverLetter: (formData) => {
    return api.post('/analysis/generate-cover-letter/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      }
    })
  }
}

// Resume API calls
export const resumeAPI = {
  create: (resumeData) => api.post('/resumes/', resumeData)
}

// Jobs API calls
export const jobAPI = {
  create: (jobData) => api.post('/jobs/', jobData)
}

export default api