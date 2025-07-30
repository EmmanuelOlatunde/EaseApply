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
      error.value = err.response?.data?.message || 'Login failed'
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
      return response.data
    } catch (err) {
      error.value = err.response?.data?.message || 'Registration failed'
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

  const updateProfile = async (profileData) => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await authAPI.updateProfile(profileData)
      user.value = { ...user.value, ...response.data }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.message || 'Profile update failed'
      throw err
    } finally {
      isLoading.value = false
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
    updateProfile
  }
})