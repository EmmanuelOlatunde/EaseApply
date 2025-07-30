<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
      <div class="p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-semibold text-ash-800">
            {{ isLogin ? 'Sign In' : 'Create Account' }}
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
        
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div v-if="!isLogin">
            <label class="block text-sm font-medium text-ash-700 mb-1">Full Name</label>
            <input
              v-model="form.fullName"
              type="text"
              required
              class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your full name"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-ash-700 mb-1">Email</label>
            <input
              v-model="form.email"
              type="email"
              required
              class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your email"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-ash-700 mb-1">Password</label>
            <input
              v-model="form.password"
              type="password"
              required
              class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your password"
            />
          </div>
          
          <div v-if="!isLogin">
            <label class="block text-sm font-medium text-ash-700 mb-1">Confirm Password</label>
            <input
              v-model="form.confirmPassword"
              type="password"
              required
              class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Confirm your password"
            />
          </div>
          
          <div v-if="error" class="text-red-600 text-sm">{{ error }}</div>
          
          <button
            type="submit"
            :disabled="isLoading"
            class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="isLoading" class="flex items-center justify-center">
              <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
              {{ isLogin ? 'Signing In...' : 'Creating Account...' }}
            </span>
            <span v-else>{{ isLogin ? 'Sign In' : 'Create Account' }}</span>
          </button>
        </form>
        
        <div class="mt-4 text-center">
          <button
            @click="toggleMode"
            class="text-blue-600 hover:text-blue-500 text-sm font-medium"
          >
            {{ isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

const props = defineProps({
  isOpen: Boolean
})

const emit = defineEmits(['close', 'success'])

const authStore = useAuthStore()
const isLogin = ref(true)
const isLoading = ref(false)
const error = ref('')

const form = ref({
  fullName: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const toggleMode = () => {
  isLogin.value = !isLogin.value
  error.value = ''
  form.value = {
    fullName: '',
    email: '',
    password: '',
    confirmPassword: ''
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
    } else {
      if (form.value.password !== form.value.confirmPassword) {
        throw new Error('Passwords do not match')
      }
      
      await authStore.register({
        email: form.value.email,
        password: form.value.password,
        full_name: form.value.fullName
      })
    }
    
    emit('success')
    emit('close')
  } catch (err) {
    error.value = err.message || (isLogin.value ? 'Login failed' : 'Registration failed')
  } finally {
    isLoading.value = false
  }
}
</script>