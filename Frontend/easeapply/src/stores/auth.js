import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '../services/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('access_token'))
  const refreshToken = ref(localStorage.getItem('refresh_token'))
  const isLoading = ref(false)
  const error = ref(null)

  const isAuthenticated = computed(() => !!token.value)

  const login = async (credentials) => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await authAPI.login(credentials)
      const { access, refresh, user: userData } = response.data
      
      token.value = access
      refreshToken.value = refresh
      user.value = userData
      
      localStorage.setItem('access_token', access)
      localStorage.setItem('refresh_token', refresh)
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.message || err.response?.data?.detail || 'Login failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const register = async (userData) => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await authAPI.register(userData)
      // Registration successful - user needs to verify email before logging in
      return response.data
    } catch (err) {
      error.value = err.response?.data?.message || err.response?.data?.detail || 'Registration failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const logout = async () => {
    try {
      await authAPI.logout()
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      token.value = null
      refreshToken.value = null
      user.value = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  }

  const getProfile = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await authAPI.getProfile()
      user.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.message || err.response?.data?.detail || 'Failed to load profile'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const updateProfile = async (profileData) => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await authAPI.updateProfile(profileData)
      user.value = { ...user.value, ...response.data }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.message || err.response?.data?.detail || 'Profile update failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const partialUpdateProfile = async (profileData) => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await authAPI.partialUpdateProfile(profileData)
      user.value = { ...user.value, ...response.data }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.message || err.response?.data?.detail || 'Profile update failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const changePassword = async (passwordData) => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await authAPI.changePassword(passwordData)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.message || err.response?.data?.detail || 'Password change failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const verifyEmail = async (uidb64, token) => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await authAPI.verifyEmail(uidb64, token)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.message || err.response?.data?.detail || 'Email verification failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const resendVerification = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await authAPI.resendVerification()
      return response.data
    } catch (err) {
      error.value = err.response?.data?.message || err.response?.data?.detail || 'Failed to resend verification'
      throw err
    } finally {
      isLoading.value = false
    }
  } 

  // Initialize user from token if available
  const initializeAuth = async () => {
    if (token.value && !user.value) {
      try {
        await getProfile()
      } catch (error) {
        console.error('Failed to initialize auth:', error)
        // Clear invalid token
        logout()
      }
    }
  }

  return {
    user,
    token,
    isAuthenticated,
    isLoading,
    error,
    login,
    register,
    logout,
    getProfile,
    updateProfile,
    partialUpdateProfile,
    changePassword,
    verifyEmail,
    resendVerification,
    initializeAuth
  }
})