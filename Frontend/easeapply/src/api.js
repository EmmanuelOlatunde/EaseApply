import { ref, reactive, onMounted } from 'vue'
import { authAPI, jobAPI, resumeAPI, analysisAPI, handleAPIError, createFormData, tokenManager } from './api'

// -------------------- Global State --------------------
export const currentView = ref('login')
export const isAuthenticated = ref(false)
export const user = ref(null)

// Loading States
export const authLoading = ref(false)
export const jobLoading = ref(false)
export const resumeLoading = ref(false)
export const profileLoading = ref(false)
export const passwordLoading = ref(false)
export const generationLoading = ref(false)

// Error and Success States
export const authError = ref('')
export const authSuccess = ref('')

// Data Collections
export const jobs = ref([])
export const resumes = ref([])
export const generatedCoverLetter = ref('')
export const copied = ref(false)

// Form States
export const showJobForm = ref(false)
export const showResumeForm = ref(false)

// Selected Items
export const selectedJobId = ref('')
export const selectedResumeId = ref('')

// Toast Notifications
export const toast = reactive({
  show: false,
  message: '',
  type: 'success'
})

// -------------------- Form Data --------------------
export const loginForm = reactive({
  email: '',
  password: ''
})

export const registerForm = reactive({
  first_name: '',
  last_name: '',
  email: '',
  password: '',
  password2: ''
})

export const resetForm = reactive({
  email: ''
})

export const jobForm = reactive({
  title: '',
  company: '',
  description: ''
})

export const resumeForm = reactive({
  title: '',
  file: null
})

export const profileForm = reactive({
  first_name: '',
  last_name: '',
  email: ''
})

export const passwordForm = reactive({
  old_password: '',
  new_password: '',
  new_password2: ''
})

// -------------------- Utility Functions --------------------
let toastTimeout
export const showToast = (message, type = 'success', duration = 3000) => {
  toast.message = message
  toast.type = type
  toast.show = true
  clearTimeout(toastTimeout)
  toastTimeout = setTimeout(() => {
    toast.show = false
  }, duration)
}

export const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString()
}

const resetObject = (obj) => {
  for (const key in obj) {
    obj[key] = obj[key] instanceof File ? null : ''
  }
}

export const clearAuthForms = () => {
  resetObject(loginForm)
  resetObject(registerForm)
  resetObject(resetForm)
}

// -------------------- Authentication --------------------
export const login = async () => {
  authLoading.value = true
  authError.value = ''
  
  try {
    const response = await authAPI.login(loginForm)
    isAuthenticated.value = true
    user.value = response.data.user
    currentView.value = 'dashboard'
    initializeProfile(user.value)
    showToast('Successfully logged in!')

    await loadUserData()
  } catch (error) {
    authError.value = handleAPIError(error, 'Login failed')
  } finally {
    authLoading.value = false
  }
}

export const register = async () => {
  authLoading.value = true
  authError.value = ''
  authSuccess.value = ''
  
  try {
    await authAPI.register(registerForm)
    authSuccess.value = 'Account created successfully! Please check your email to verify your account.'
    resetObject(registerForm)
  } catch (error) {
    authError.value = handleAPIError(error, 'Registration failed')
  } finally {
    authLoading.value = false
  }
}

export const logout = async () => {
  try {
    await authAPI.logout()
    showToast('Successfully logged out!')
  } catch (error) {
    console.error('Logout error:', error)
  } finally {
    isAuthenticated.value = false
    user.value = null
    currentView.value = 'login'
    jobs.value = []
    resumes.value = []
    generatedCoverLetter.value = ''
  }
}

export const resetPassword = async () => {
  authLoading.value = true
  authError.value = ''
  
  try {
    await authAPI.resetPassword(resetForm.email)
    showToast('Password reset link sent to your email!')
    currentView.value = 'login'
  } catch (error) {
    authError.value = handleAPIError(error, 'Reset failed')
  } finally {
    authLoading.value = false
  }
}

// -------------------- Profile --------------------
export const updateProfile = async () => {
  profileLoading.value = true
  try {
    const response = await authAPI.updateProfile(profileForm)
    user.value = response.data
    showToast('Profile updated successfully!')
  } catch (error) {
    showToast(handleAPIError(error, 'Failed to update profile'), 'error')
  } finally {
    profileLoading.value = false
  }
}

export const changePassword = async () => {
  passwordLoading.value = true
  try {
    await authAPI.changePassword(passwordForm)
    showToast('Password changed successfully!')
    resetObject(passwordForm)
  } catch (error) {
    showToast(handleAPIError(error, 'Failed to change password'), 'error')
  } finally {
    passwordLoading.value = false
  }
}

// -------------------- Jobs --------------------
export const loadJobs = async () => {
  try {
    const response = await jobAPI.listAll()
    jobs.value = response.data
  } catch (error) {
    console.error('Failed to load jobs:', error)
    showToast(handleAPIError(error, 'Failed to load jobs'), 'error')
  }
}

export const createJob = async () => {
  jobLoading.value = true
  try {
    const { data } = await jobAPI.create(jobForm)
    jobs.value = [...jobs.value, data]
    showToast('Job added successfully!')
    showJobForm.value = false
    resetObject(jobForm)
  } catch (error) {
    showToast(handleAPIError(error, 'Failed to add job'), 'error')
  } finally {
    jobLoading.value = false
  }
}

export const deleteJob = async (jobId) => {
  try {
    await jobAPI.delete(jobId)
    jobs.value = jobs.value.filter(job => job.id !== jobId)
    showToast('Job deleted successfully!')
  } catch (error) {
    showToast(handleAPIError(error, 'Failed to delete job'), 'error')
  }
}

// -------------------- Resumes --------------------
export const loadResumes = async () => {
  try {
    const response = await resumeAPI.list()
    resumes.value = response.data.results || response.data
  } catch (error) {
    console.error('Failed to load resumes:', error)
    showToast(handleAPIError(error, 'Failed to load resumes'), 'error')
  }
}

export const handleResumeFileChange = (event) => {
  resumeForm.file = event.target.files[0]
}

export const uploadResume = async () => {
  if (!resumeForm.file || !resumeForm.title) {
    showToast('Please provide both title and file', 'error')
    return
  }

  resumeLoading.value = true
  try {
    const formData = createFormData(resumeForm)
    const response = await resumeAPI.upload(formData)
    resumes.value = [...resumes.value, response.data]
    showToast('Resume uploaded successfully!')
    showResumeForm.value = false
    resetObject(resumeForm)
  } catch (error) {
    showToast(handleAPIError(error, 'Failed to upload resume'), 'error')
  } finally {
    resumeLoading.value = false
  }
}

export const deleteResume = async (resumeId) => {
  try {
    await resumeAPI.delete(resumeId)
    resumes.value = resumes.value.filter(resume => resume.id !== resumeId)
    showToast('Resume deleted successfully!')
  } catch (error) {
    showToast(handleAPIError(error, 'Failed to delete resume'), 'error')
  }
}

// -------------------- Cover Letter --------------------
export const generateCoverLetter = async () => {
  if (!selectedResumeId.value || !selectedJobId.value) {
    showToast('Please select both a resume and a job', 'error')
    return
  }

  generationLoading.value = true
  generatedCoverLetter.value = ''
  
  try {
    const { data } = await analysisAPI.generateCoverLetter({
      resume_id: selectedResumeId.value,
      job_id: selectedJobId.value
    })
    generatedCoverLetter.value = data.cover_letter
    showToast('Cover letter generated successfully!')
  } catch (error) {
    showToast(handleAPIError(error, 'Failed to generate cover letter'), 'error')
  } finally {
    generationLoading.value = false
  }
}

export const copyCoverLetter = async () => {
  try {
    await navigator.clipboard.writeText(generatedCoverLetter.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
    showToast('Cover letter copied to clipboard!')
  } catch {
    showToast('Failed to copy to clipboard', 'error')
  }
}

const downloadElement = document.createElement('a')
export const downloadCoverLetter = () => {
  if (!generatedCoverLetter.value) {
    showToast('No cover letter to download', 'error')
    return
  }
  const blob = new Blob([generatedCoverLetter.value], { type: 'text/plain' })
  downloadElement.href = URL.createObjectURL(blob)
  downloadElement.download = 'cover-letter.txt'
  downloadElement.click()
  URL.revokeObjectURL(downloadElement.href)
  showToast('Cover letter downloaded!')
}

// -------------------- Helpers --------------------
export const loadUserData = async () => {
  await Promise.all([loadJobs(), loadResumes()])
}

export const initializeProfile = (userData) => {
  if (userData) {
    profileForm.first_name = userData.first_name || ''
    profileForm.last_name = userData.last_name || ''
    profileForm.email = userData.email || ''
  }
}

export const checkAuthStatus = async () => {
  const token = tokenManager.getAccessToken()
  if (!token) {
    isAuthenticated.value = false
    return false
  }

  try {
    const [profileRes] = await Promise.all([
      authAPI.getProfile(),
      loadUserData()
    ])
    user.value = profileRes.data
    isAuthenticated.value = true
    currentView.value = 'dashboard'
    initializeProfile(user.value)
    return true
  } catch {
    tokenManager.clearTokens()
    isAuthenticated.value = false
    user.value = null
    return false
  }
}

export const initializeApp = async () => {
  await checkAuthStatus()
}

// -------------------- Auto-init --------------------
onMounted(() => {
  initializeApp()
})
