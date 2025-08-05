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
  getProfile: () => api.get('/users/profile/'),
  updateProfile: (profileData) => api.put('/users/profile/', profileData),
  partialUpdateProfile: (profileData) => api.patch('/users/profile/', profileData),
  resendVerification: (email) => api.post('/users/resend-verification/', { email }),
  resetPasswordConfirm: (resetData) => api.post('/users/reset-password-confirm/', resetData),
  verifyEmail: (uidb64, token) => api.get(`/users/email-verify/${uidb64}/${token}/`)
}

// Analysis API calls
export const analysisAPI = {
  generateCoverLetter: (data) => {
    return api.post('/analysis/generate-cover-letter/', data, {
      timeout: 60000, // 60 seconds for AI generation
      headers: {
        'Content-Type': 'application/json'
      }
    })
  }
}

// Resume API calls
export const resumeAPI = {
  list: (page = 1) => api.get(`/resumes/?page=${page}`),
  upload: (formData) => {
    return api.post('/resumes/', formData, {
      headers: { 
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  get: (resumeId) => api.get(`/resumes/${resumeId}/`),
  reparse: (resumeId) => api.put(`/resumes/${resumeId}/reparse/`),
  analytics: (page = 1) => api.get(`/resumes/analytics/?page=${page}`)
}

// Jobs API calls
export const jobAPI = {
  list: (page = 1) => api.get(`/jobs/my-jobs/?page=${page}`),
  create: (jobData) => api.post('/jobs/', jobData),
  get: (jobId) => api.get(`/jobs/${jobId}/`),
  update: (jobId, jobData) => api.put(`/jobs/${jobId}/`, jobData),
  delete: (jobId) => api.delete(`/jobs/${jobId}/`),
  reprocess: (jobId, jobData) => api.put(`/jobs/reprocess/${jobId}/`, jobData)
}

export default api