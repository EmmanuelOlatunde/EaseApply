<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
      <div class="p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-semibold text-ash-800">
            {{ isForgotPassword ? 'Reset Password' : (isLogin ? 'Sign In' : 'Create Account') }}
          </h2>
          <button
            @click="$emit('close')"
            class="text-ash-500 hover:text-ash-700"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <!-- Success message for registration -->
        <div v-if="registrationSuccess" class="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg class="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-green-800">Account created successfully!</h3>
              <div class="mt-2 text-sm text-green-700">
                <p>A verification email has been sent to your email address. Please check your inbox and click the verification link to activate your account.</p>
              </div>
              <div class="mt-3">
                <button
                  @click="resendVerification"
                  :disabled="isResending"
                  class="text-sm text-green-600 hover:text-green-500 font-medium disabled:opacity-50"
                >
                  {{ isResending ? 'Resending...' : "Didn't receive email? Resend verification" }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Success message for password reset -->
        <div v-if="resetPasswordSuccess" class="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg class="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-green-800">Reset link sent!</h3>
              <div class="mt-2 text-sm text-green-700">
                <p>If an account with that email exists, we've sent a password reset link to your email address.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Forgot Password Form -->
        <form v-if="isForgotPassword && !resetPasswordSuccess" @submit.prevent="handleForgotPassword" class="space-y-5">
          <div class="text-center mb-4">
            <p class="text-sm text-gray-600">
              Enter your email address and we'll send you a link to reset your password.
            </p>
          </div>

          <!-- Email field -->
          <div class="mb-5">
            <label class="block text-sm font-medium text-gray-700 mb-2">Email Address *</label>
            <input
              v-model="form.email"
              type="email"
              required
              class="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
              placeholder="Enter your email address"
            />
          </div>
          
          <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4">
            <div class="text-red-600 text-sm">{{ error }}</div>
          </div>
          
          <button
            type="submit"
            :disabled="isLoading"
            class="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            <span v-if="isLoading" class="flex items-center justify-center">
              <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
              Sending Reset Link...
            </span>
            <span v-else>Send Reset Link</span>
          </button>
        </form>
        
        <form v-if="!registrationSuccess && !resetPasswordSuccess && !isForgotPassword" @submit.prevent="handleSubmit" class="space-y-5">
          <!-- Registration fields -->
          <div v-if="!isLogin">
            <!-- Name fields -->
            <div class="grid grid-cols-2 gap-4 mb-5">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">First Name *</label>
                <input
                  v-model="form.first_name"
                  type="text"
                  required
                  class="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                  placeholder="First name"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Last Name *</label>
                <input
                  v-model="form.last_name"
                  type="text"
                  required
                  class="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                  placeholder="Last name"
                />
              </div>
            </div>
            
            <!-- Username field -->
            <div class="mb-5">
              <label class="block text-sm font-medium text-gray-700 mb-2">Username *</label>
              <input
                v-model="form.username"
                type="text"
                required
                class="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                placeholder="Choose a username"
              />
              <p class="text-xs text-gray-500 mt-1.5">150 characters or fewer. Letters, digits and @/./+/-/_ only.</p>
            </div>
          </div>
          
          <!-- Email field -->
          <div class="mb-5">
            <label class="block text-sm font-medium text-gray-700 mb-2">Email Address *</label>
            <input
              v-model="form.email"
              type="email"
              required
              class="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
              placeholder="Enter your email"
            />
          </div>
          
          <!-- Phone field (registration only) -->
          <div v-if="!isLogin" class="mb-5">
            <label class="block text-sm font-medium text-gray-700 mb-2">Phone Number</label>
            <input
              v-model="form.phone"
              type="tel"
              pattern="^\+?1?\d{9,15}$"
              class="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
              placeholder="e.g., +1234567890"
            />
            <p class="text-xs text-gray-500 mt-1.5">Optional. Include country code for international numbers.</p>
          </div>
          
          <!-- Password fields -->
          <div class="space-y-5">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Password *</label>
              <input
                v-model="form.password"
                type="password"
                required
                class="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                placeholder="Enter your password"
              />
            </div>
            
            <div v-if="!isLogin">
              <label class="block text-sm font-medium text-gray-700 mb-2">Confirm Password *</label>
              <input
                v-model="form.password_confirm"
                type="password"
                required
                class="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                placeholder="Confirm your password"
              />
            </div>
          </div>

          <!-- Forgot Password Link (login only) -->
          <div v-if="isLogin" class="text-right">
            <button
              type="button"
              @click="goToForgotPassword"
              class="text-sm text-blue-600 hover:text-blue-500 font-medium"
            >
              Forgot your password?
            </button>
          </div>
          
          <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4">
            <div class="text-red-600 text-sm">
              <div v-if="typeof error === 'object'">
                <div v-for="(messages, field) in error" :key="field" class="mb-1 last:mb-0">
                  <span v-if="formatFieldName(field)" class="font-medium">{{ formatFieldName(field) }}:</span>
                  {{ Array.isArray(messages) ? messages.join(', ') : messages }}
                </div>
              </div>
              <div v-else>{{ error }}</div>
            </div>
          </div>
          
          <button
            type="submit"
            :disabled="isLoading"
            class="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            <span v-if="isLoading" class="flex items-center justify-center">
              <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
              {{ isLogin ? 'Signing In...' : 'Creating Account...' }}
            </span>
            <span v-else>{{ isLogin ? 'Sign In' : 'Create Account' }}</span>
          </button>
        </form>
        
        <div v-if="!registrationSuccess && !resetPasswordSuccess" class="mt-4 text-center">
          <div v-if="isForgotPassword">
            <button
              @click="goToLogin"
              class="text-blue-600 hover:text-blue-500 text-sm font-medium"
            >
              ← Back to Sign In
            </button>
          </div>
          <div v-else>
            <button
              @click="toggleMode"
              class="text-blue-600 hover:text-blue-500 text-sm font-medium"
            >
              {{ isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in" }}
            </button>
          </div>
        </div>
        
        <div v-if="registrationSuccess" class="mt-4 text-center">
          <button
            @click="goToLogin"
            class="text-blue-600 hover:text-blue-500 text-sm font-medium"
          >
            Go to Sign In
          </button>
        </div>

        <div v-if="resetPasswordSuccess" class="mt-4 text-center">
          <button
            @click="goToLogin"
            class="text-blue-600 hover:text-blue-500 text-sm font-medium"
          >
            Back to Sign In
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { authAPI } from '../services/api'

const props = defineProps({
  isOpen: Boolean
})

const emit = defineEmits(['close', 'success'])

const authStore = useAuthStore()
const isLogin = ref(true)
const isForgotPassword = ref(false)
const isLoading = ref(false)
const isResending = ref(false)
const error = ref('')
const registrationSuccess = ref(false)
const resetPasswordSuccess = ref(false)

const form = ref({
  first_name: '',
  last_name: '',
  username: '',
  email: '',
  phone: '',
  password: '',
  password_confirm: ''
})

const formatFieldName = (field) => {
  const fieldNames = {
    'first_name': 'First Name',
    'last_name': 'Last Name',
    'username': 'Username',
    'email': 'Email',
    'phone': 'Phone',
    'password': 'Password',
    'password_confirm': 'Confirm Password',
    'non_field_errors': ''
  }
  return fieldNames[field] || field
}

const toggleMode = () => {
  isLogin.value = !isLogin.value
  isForgotPassword.value = false
  error.value = ''
  registrationSuccess.value = false
  resetPasswordSuccess.value = false
  form.value = {
    first_name: '',
    last_name: '',
    username: '',
    email: '',
    phone: '',
    password: '',
    password_confirm: ''
  }
}

const goToLogin = () => {
  registrationSuccess.value = false
  resetPasswordSuccess.value = false
  isForgotPassword.value = false
  isLogin.value = true
  error.value = ''
  form.value = {
    first_name: '',
    last_name: '',
    username: '',
    email: '',
    phone: '',
    password: '',
    password_confirm: ''
  }
}

const goToForgotPassword = () => {
  isForgotPassword.value = true
  isLogin.value = false
  error.value = ''
  registrationSuccess.value = false
  resetPasswordSuccess.value = false
  // Keep email if already entered
  form.value = {
    first_name: '',
    last_name: '',
    username: '',
    email: form.value.email || '',
    phone: '',
    password: '',
    password_confirm: ''
  }
}

const resendVerification = async () => {
  if (!form.value.email) return
  
  isResending.value = true
  try {
    await authAPI.resendVerification(form.value.email)
    // You might want to show a success message here
  } catch (err) {
    console.error('Failed to resend verification:', err)
    // You might want to show an error message here
  } finally {
    isResending.value = false
  }
}

const handleForgotPassword = async () => {
  error.value = ''
  isLoading.value = true
  
  try {
    await authAPI.resetPassword(form.value.email)
    resetPasswordSuccess.value = true
  } catch (err) {
    console.error('Password reset error:', err)
    error.value = err.response?.data?.message || err.response?.data?.detail || 'Failed to send reset email'
  } finally {
    isLoading.value = false
  }
}

const handleSubmit = async () => {
  error.value = ''
  isLoading.value = true
  
  try {
    if (isLogin.value) {
      await authStore.login({
        email: form.value.email,
        password: form.value.password
      })
      emit('success')
      emit('close')
    } else {
      // Client-side validation for registration
      if (form.value.password !== form.value.password_confirm) {
        throw new Error('Passwords do not match')
      }

      // Prepare registration data
      const registrationData = {
        email: form.value.email,
        username: form.value.username,
        password: form.value.password,
        password_confirm: form.value.password_confirm,
        first_name: form.value.first_name,
        last_name: form.value.last_name
      }

      // Add phone if provided
      if (form.value.phone.trim()) {
        registrationData.phone = form.value.phone.trim()
      }
      
      await authStore.register(registrationData)
      
      // Show success message instead of closing modal
      registrationSuccess.value = true
    }
  } catch (err) {
    console.error('Auth error:', err)
    
    // Handle different types of errors
    if (err.response?.data) {
      const errorData = err.response.data
      
      if (errorData.non_field_errors) {
        error.value = Array.isArray(errorData.non_field_errors) 
          ? errorData.non_field_errors.join(', ') 
          : errorData.non_field_errors
      }
      // Handle other validation errors
      else if (typeof errorData === 'object' && !errorData.message) {
        // Validation errors from API
        error.value = errorData
      } else {
        // Single error message
        error.value = errorData.message || errorData.detail || 'An error occurred'
      }
    } else if (err.message) {
      error.value = err.message
    } else {
      error.value = isLogin.value ? 'Login failed' : 'Registration failed'
    }
  } finally {
    isLoading.value = false
  }
}
</script>