<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
      <div class="text-center mb-6">
        <h2 class="text-xl font-semibold text-ash-800">Reset Your Password</h2>
        <p class="text-sm text-gray-600 mt-2">Enter your new password below</p>
      </div>

      <!-- Success message -->
      <div v-if="success" class="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-green-800">Password reset successful!</h3>
            <div class="mt-2 text-sm text-green-700">
              <p>{{ success }}</p>
            </div>
            <div class="mt-3">
              <router-link 
                to="/" 
                class="text-sm text-green-600 hover:text-green-500 font-medium"
              >
                Go to Sign In →
              </router-link>
            </div>
          </div>
        </div>
      </div>

      <form v-if="!success" @submit.prevent="submitReset" class="space-y-5">
        <!-- New Password field -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">New Password *</label>
          <input
            v-model="newPassword"
            type="password"
            required
            minlength="8"
            class="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
            placeholder="Enter your new password"
          />
          <p class="text-xs text-gray-500 mt-1.5">Must be at least 8 characters long.</p>
        </div>

        <!-- Confirm Password field -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Confirm New Password *</label>
          <input
            v-model="confirmPassword"
            type="password"
            required
            minlength="8"
            class="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
            placeholder="Confirm your new password"
          />
        </div>

        <!-- Error message -->
        <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4">
          <div class="text-red-600 text-sm">
            <div v-if="typeof error === 'object'">
              <div v-for="(messages, field) in error" :key="field" class="mb-1 last:mb-0">
                <strong>{{ formatFieldName(field) }}:</strong> {{ Array.isArray(messages) ? messages.join(', ') : messages }}
              </div>
            </div>
            <div v-else>{{ error }}</div>
          </div>
        </div>

        <!-- Submit button -->
        <button
          type="submit"
          :disabled="loading || !uid || !token"
          class="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          <span v-if="loading" class="flex items-center justify-center">
            <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
            Resetting Password...
          </span>
          <span v-else>Reset Password</span>
        </button>
      </form>

      <!-- Invalid link message -->
      <div v-if="!uid || !token" class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div class="text-yellow-800 text-sm text-center">
          <p class="font-medium">Invalid or expired reset link</p>
          <p class="mt-2">Please request a new password reset link.</p>
          <router-link 
            to="/forgot-password" 
            class="inline-block mt-3 text-blue-600 hover:text-blue-500 font-medium"
          >
            Request new reset link →
          </router-link>
        </div>
      </div>

      <!-- Back to login link -->
      <div v-if="!success" class="mt-6 text-center">
        <router-link 
          to="/login" 
          class="text-blue-600 hover:text-blue-500 text-sm font-medium"
        >
          ← Back to Sign In
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authAPI } from '../services/api'

const route = useRoute()
const router = useRouter()

const uid = ref('')
const token = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')

const formatFieldName = (field) => {
  const fieldNames = {
    'new_password': 'New Password',
    'new_password_confirm': 'Confirm Password',
    'uid': 'User ID',
    'token': 'Reset Token'
  }
  return fieldNames[field] || field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

onMounted(() => {
  // Get parameters from URL path or query
  uid.value = route.params.uid || route.query.uid || ''
  token.value = route.params.token || route.query.token || ''
  
  if (!uid.value || !token.value) {
    console.warn('Password reset parameters missing from URL')
  }
})

const submitReset = async () => {
  loading.value = true
  error.value = ''
  success.value = ''

  // Validation
  if (!uid.value || !token.value) {
    error.value = 'Invalid or missing reset link parameters.'
    loading.value = false
    return
  }

  if (newPassword.value !== confirmPassword.value) {
    error.value = 'Passwords do not match.'
    loading.value = false
    return
  }

  if (newPassword.value.length < 8) {
    error.value = 'Password must be at least 8 characters long.'
    loading.value = false
    return
  }

  try {
    const resetData = {
      uid: uid.value,
      token: token.value,
      new_password: newPassword.value,
      new_password_confirm: confirmPassword.value
    }

    await authAPI.resetPasswordConfirm(resetData)
    
    success.value = 'Your password has been successfully reset. You can now sign in with your new password.'
    
    // Clear form
    newPassword.value = ''
    confirmPassword.value = ''
    
    // Optional: Auto-redirect after a delay
    setTimeout(() => {
      router.push('/login')
    }, 5000)
    
  } catch (err) {
    console.error('Password reset error:', err)
    
    // Handle different types of errors
    if (err.response?.data) {
      const errorData = err.response.data
      if (typeof errorData === 'object' && !errorData.message && !errorData.detail) {
        // Validation errors from API
        error.value = errorData
      } else {
        // Single error message
        error.value = errorData.message || errorData.detail || errorData.error || 'Password reset failed'
      }
    } else if (err.message) {
      error.value = err.message
    } else {
      error.value = 'Password reset failed. Please try again.'
    }
  } finally {
    loading.value = false
  }
}
</script>