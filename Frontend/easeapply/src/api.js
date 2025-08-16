import { ref, reactive, onMounted, computed } from 'vue'
import axios from 'axios'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Global State
const currentView = ref('login')
const isAuthenticated = ref(false)
const user = ref(null)
const authToken = ref(localStorage.getItem('authToken') || '')

// Loading States
const authLoading = ref(false)
const jobLoading = ref(false)
const resumeLoading = ref(false)
const profileLoading = ref(false)
const passwordLoading = ref(false)
const generationLoading = ref(false)

// Error States
const authError = ref('')
const authSuccess = ref('')

// Data Collections
const jobs = ref([])
const resumes = ref([])
const generatedCoverLetter = ref('')
const copied = ref(false)

// Form States
const showJobForm = ref(false)
const showResumeForm = ref(false)

// Selected Items
const selectedJobId = ref('')
const selectedResumeId = ref('')

// Toast Notifications
const toast = reactive({
  show: false,
  message: '',
  type: 'success'
})

// Form Data
const loginForm = reactive({
  email: '',
  password: ''
})

const registerForm = reactive({
  first_name: '',
  last_name: '',
  email: '',
  password: '',
  password2: ''
})

const resetForm = reactive({
  email: ''
})

const jobForm = reactive({
  title: '',
  company: '',
  description: ''
})

const resumeForm = reactive({
  title: '',
  file: null
})

const profileForm = reactive({
  first_name: '',
  last_name: '',
  email: ''
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  new_password2: ''
})

// Axios Configuration
axios.defaults.baseURL = `${API_BASE_URL}/api`

axios.interceptors.request.use((config) => {
  if (authToken.value) {
    config.headers.Authorization = `Bearer ${authToken.value}`
  }
  return config
})

// Utility Functions
const showToast = (message, type = 'success') => {
  toast.message = message
  toast.type = type
  toast.show = true
  setTimeout(() => {
    toast.show = false
  }, 3000)
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString()
}

// Authentication Functions
const login = async () => {
  authLoading.value = true
  authError.value = ''
  
  try {
    const response = await axios.post('/users/login/', loginForm)
    authToken.value = response.data.access
    localStorage.setItem('authToken', authToken.value)
    isAuthenticated.value = true
    user.value = response.data.user
    currentView.value = 'dashboard'
    showToast('Successfully logged in!')
    await loadUserData()
  } catch (error) {
    authError.value = error.response?.data?.detail || 'Login failed'
  } finally {
    authLoading.value = false
  }
}

const register = async () => {
  authLoading.value = true
  authError.value = ''
  authSuccess.value = ''
  
  try {
    await axios.post('/users/register/', registerForm)
    authSuccess.value = 'Account created successfully! Please check your email to verify your account.'
    Object.keys(registerForm).forEach(key => registerForm[key] = '')
  } catch (error) {
    authError.value = error.response?.data?.detail || 'Registration failed'
  } finally {
    authLoading.value = false
  }
}

const logout = async () => {
  try {
    await axios.post('/users/logout/')
  } catch (error) {
    console.error('Logout error:', error)
  } finally {
    authToken.value = ''
    localStorage.removeItem('authToken')
    isAuthenticated.value = false
    user.value = null
    currentView.value = 'login'
    showToast('Successfully logged out!')
  }
}

const resetPassword = async () => {
  authLoading.value = true
  authError.value = ''
  
  try {
    await axios.post('/users/reset-password/', resetForm)
    showToast('Password reset link sent to your email!')
    currentView.value = 'login'
  } catch (error) {
    authError.value = error.response?.data?.detail || 'Reset failed'
  } finally {
    authLoading.value = false
  }
}

// Profile Functions
const updateProfile = async () => {
  profileLoading.value = true
  
  try {
    const response = await axios.put('/users/profile/', profileForm)
    user.value = response.data
    showToast('Profile updated successfully!')
  } catch (error) {
    showToast('Failed to update profile', 'error')
  } finally {
    profileLoading.value = false
  }
}

const changePassword = async () => {
  passwordLoading.value = true
  
  try {
    await axios.put('/users/change-password/', passwordForm)
    showToast('Password changed successfully!')
    Object.keys(passwordForm).forEach(key => passwordForm[key] = '')
  } catch (error) {
    showToast('Failed to change password', 'error')
  } finally {
    passwordLoading.value = false
  }
}

// Job Functions
const loadJobs = async () => {
  try {
    const response = await axios.get('/jobs/')
    jobs.value = response.data
  } catch (error) {
    console.error('Failed to load jobs:', error)
  }
}

const createJob = async () => {
  jobLoading.value = true
  
  try {
    const response = await axios.post('/jobs/', jobForm)
    jobs.value.push(response.data)
    showToast('Job added successfully!')
    showJobForm.value = false
    resetJobForm()
  } catch (error) {
    showToast('Failed to add job', 'error')
  } finally {
    jobLoading.value = false
  }
}

const resetJobForm = () => {
  Object.keys(jobForm).forEach(key => jobForm[key] = '')
}

// Resume Functions
const loadResumes = async () => {
  try {
    const response = await axios.get('/resumes/')
    resumes.value = response.data
  } catch (error) {
    console.error('Failed to load resumes:', error)
  }
}

const handleResumeFileChange = (event) => {
  resumeForm.file = event.target.files[0]
}

const uploadResume = async () => {
  resumeLoading.value = true
  
  try {
    const formData = new FormData()
    formData.append('title', resumeForm.title)
    formData.append('file', resumeForm.file)
    
    const response = await axios.post('/resumes/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    resumes.value.push(response.data)
    showToast('Resume uploaded successfully!')
    showResumeForm.value = false
    resetResumeForm()
  } catch (error) {
    showToast('Failed to upload resume', 'error')
  } finally {
    resumeLoading.value = false
  }
}

const resetResumeForm = () => {
  resumeForm.title = ''
  resumeForm.file = null
  if (this.$refs.resumeFileInput) {
    this.$refs.resumeFileInput.value = ''
  }
}

// Cover Letter Generation
const generateCoverLetter = async () => {
  generationLoading.value = true
  generatedCoverLetter.value = ''
  
  try {
    const response = await axios.post('/analysis/generate-cover-letter/', {
      resume_id: selectedResumeId.value,
      job_id: selectedJobId.value
    })
    
    generatedCoverLetter.value = response.data.cover_letter
    showToast('Cover letter generated successfully!')
  } catch (error) {
    showToast('Failed to generate cover letter', 'error')
  } finally {
    generationLoading.value = false
  }
}

const copyCoverLetter = async () => {
  try {
    await navigator.clipboard.writeText(generatedCoverLetter.value)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
    showToast('Cover letter copied to clipboard!')
  } catch (error) {
    showToast('Failed to copy to clipboard', 'error')
  }
}

const downloadCoverLetter = () => {
  const blob = new Blob([generatedCoverLetter.value], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'cover-letter.txt'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// Load User Data
const loadUserData = async () => {
  await Promise.all([
    loadJobs(),
    loadResumes()
  ])
}

// Check Authentication on Mount
onMounted(async () => {
  if (authToken.value) {
    try {
      const response = await axios.get('/users/profile/')
      user.value = response.data
      isAuthenticated.value = true
      currentView.value = 'dashboard'
      
      // Load profile form data
      profileForm.first_name = user.value.first_name
      profileForm.last_name = user.value.last_name
      profileForm.email = user.value.email
      
      await loadUserData()
    } catch (error) {
      // Token is invalid
      authToken.value = ''
      localStorage.removeItem('authToken')
      isAuthenticated.value = false
    }
  }
})
