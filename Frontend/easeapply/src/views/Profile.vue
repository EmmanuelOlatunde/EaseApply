<template>
  <div class="min-h-screen bg-ash-50">
    <!-- Header -->
    <header class="bg-white border-b border-ash-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <div class="flex items-center">
            <router-link to="/" class="text-xl font-bold text-ash-800">EASEAPPLY AI</router-link>
          </div>
          <nav class="flex items-center space-x-4">
            <router-link
              to="/"
              class="text-ash-600 hover:text-ash-800 px-3 py-2 rounded-md text-sm font-medium"
            >
              Generator
            </router-link>
            <router-link
              to="/dashboard"
              class="text-ash-600 hover:text-ash-800 px-3 py-2 rounded-md text-sm font-medium"
            >
              Dashboard
            </router-link>
            <button
              @click="handleLogout"
              class="text-ash-600 hover:text-ash-800 px-3 py-2 rounded-md text-sm font-medium"
            >
              Logout
            </button>
          </nav>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-ash-900">Profile Settings</h1>
        <p class="text-ash-600 mt-2">Manage your account information and preferences.</p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Navigation -->
        <div class="lg:col-span-1">
          <nav class="bg-white rounded-lg shadow-sm border border-ash-200 p-4">
            <ul class="space-y-2">
              <li>
                <button
                  @click="activeTab = 'profile'"
                  class="w-full text-left px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200"
                  :class="activeTab === 'profile' ? 'bg-blue-100 text-blue-700' : 'text-ash-600 hover:text-ash-800 hover:bg-ash-50'"
                >
                  Profile Information
                </button>
              </li>
              <li>
                <button
                  @click="activeTab = 'password'"
                  class="w-full text-left px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200"
                  :class="activeTab === 'password' ? 'bg-blue-100 text-blue-700' : 'text-ash-600 hover:text-ash-800 hover:bg-ash-50'"
                >
                  Change Password
                </button>
              </li>
              
            </ul>
          </nav>
        </div>

        <!-- Content -->
        <div class="lg:col-span-2">
          <!-- Profile Information -->
          <div v-if="activeTab === 'profile'" class="bg-white rounded-lg shadow-sm border border-ash-200 p-6">
            <h2 class="text-lg font-semibold text-ash-800 mb-6">Profile Information</h2>
            
            <form @submit.prevent="updateProfile" class="space-y-6">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label class="block text-sm font-medium text-ash-700 mb-2">Username</label>
                  <input
                    v-model="profileForm.username"
                    type="text"
                    class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter your username"
                    required
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-ash-700 mb-2">Email</label>
                  <input
                    v-model="profileForm.email"
                    type="email"
                    class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-ash-50"
                    placeholder="Enter your email"
                    readonly
                  />
                  <p class="text-xs text-ash-500 mt-1">Email cannot be changed</p>
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label class="block text-sm font-medium text-ash-700 mb-2">First Name</label>
                  <input
                    v-model="profileForm.first_name"
                    type="text"
                    class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter your first name"
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-ash-700 mb-2">Last Name</label>
                  <input
                    v-model="profileForm.last_name"
                    type="text"
                    class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter your last name"
                  />
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-ash-700 mb-2">Phone Number</label>
                <input
                  v-model="profileForm.phone"
                  type="tel"
                  class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your phone number"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-ash-700 mb-2">Date of Birth</label>
                <input
                  v-model="profileForm.date_of_birth"
                  type="date"
                  class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-ash-700 mb-2">Bio</label>
                <textarea
                  v-model="profileForm.bio"
                  rows="4"
                  class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Tell us about yourself (max 500 characters)"
                  maxlength="500"
                ></textarea>
                <p class="text-xs text-ash-500 mt-1">{{ profileForm.bio.length }}/500 characters</p>
              </div>

              <div v-if="profileError" class="text-red-600 text-sm">{{ profileError }}</div>
              <div v-if="profileSuccess" class="text-green-600 text-sm">{{ profileSuccess }}</div>

              <div class="flex justify-end">
                <button
                  type="submit"
                  :disabled="isUpdatingProfile"
                  class="px-6 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span v-if="isUpdatingProfile">Updating...</span>
                  <span v-else>Update Profile</span>
                </button>
              </div>
            </form>
          </div>

          <!-- Change Password -->
          <div v-if="activeTab === 'password'" class="bg-white rounded-lg shadow-sm border border-ash-200 p-6">
            <h2 class="text-lg font-semibold text-ash-800 mb-6">Change Password</h2>
            
            <form @submit.prevent="changePassword" class="space-y-6">
              <div>
                <label class="block text-sm font-medium text-ash-700 mb-2">Current Password</label>
                <input
                  v-model="passwordForm.old_password"
                  type="password"
                  class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter current password"
                  required
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-ash-700 mb-2">New Password</label>
                <input
                  v-model="passwordForm.new_password"
                  type="password"
                  class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter new password"
                  required
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-ash-700 mb-2">Confirm New Password</label>
                <input
                  v-model="passwordForm.new_password_confirm"
                  type="password"
                  class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Confirm new password"
                  required
                />
              </div>

              <div v-if="passwordError" class="text-red-600 text-sm">{{ passwordError }}</div>
              <div v-if="passwordSuccess" class="text-green-600 text-sm">{{ passwordSuccess }}</div>

              <div class="flex justify-end">
                <button
                  type="submit"
                  :disabled="isChangingPassword"
                  class="px-6 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span v-if="isChangingPassword">Changing...</span>
                  <span v-else>Change Password</span>
                </button>
              </div>
            </form>
          </div>

          
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import { authAPI } from '../services/api'

const authStore = useAuthStore()
const router = useRouter()

const activeTab = ref('profile')

// Profile form - updated to match API schema
const profileForm = ref({
  username: '',
  email: '',
  first_name: '',
  last_name: '',
  phone: '',
  date_of_birth: '',
  bio: ''
})

const isUpdatingProfile = ref(false)
const profileError = ref('')
const profileSuccess = ref('')

// Password form - updated to match API schema
const passwordForm = ref({
  old_password: '',
  new_password: '',
  new_password_confirm: ''
})

const isChangingPassword = ref(false)
const passwordError = ref('')
const passwordSuccess = ref('')

// Preferences form
const preferencesForm = ref({
  defaultTone: 'professional',
  defaultLength: 'medium',
  emailNotifications: {
    generation: true,
    tips: false
  }
})

const isUpdatingPreferences = ref(false)
const preferencesError = ref('')
const preferencesSuccess = ref('')

const handleLogout = async () => {
  await authStore.logout()
  router.push('/')
}

const updateProfile = async () => {
  profileError.value = ''
  profileSuccess.value = ''
  isUpdatingProfile.value = true

  try {
    // Create payload with only the fields that can be updated
    const payload = {
      username: profileForm.value.username,
      first_name: profileForm.value.first_name,
      last_name: profileForm.value.last_name,
      phone: profileForm.value.phone,
      date_of_birth: profileForm.value.date_of_birth || null,
      bio: profileForm.value.bio
    }

    const response = await authAPI.updateProfile(payload)
    
    // Update the user in the store
    authStore.user = { ...authStore.user, ...response.data }
    
    profileSuccess.value = 'Profile updated successfully!'
    
    setTimeout(() => {
      profileSuccess.value = ''
    }, 3000)
    
  } catch (err) {
    console.error('Profile update error:', err)
    if (err.response?.data) {
      // Handle validation errors
      const errors = err.response.data
      if (typeof errors === 'object') {
        const errorMessages = Object.values(errors).flat().join(', ')
        profileError.value = errorMessages
      } else {
        profileError.value = errors.message || 'Failed to update profile'
      }
    } else {
      profileError.value = 'Failed to update profile'
    }
  } finally {
    isUpdatingProfile.value = false
  }
}

const changePassword = async () => {
  passwordError.value = ''
  passwordSuccess.value = ''

  if (passwordForm.value.new_password !== passwordForm.value.new_password_confirm) {
    passwordError.value = 'New passwords do not match'
    return
  }

  if (passwordForm.value.new_password.length < 8) {
    passwordError.value = 'New password must be at least 8 characters long'
    return
  }

  isChangingPassword.value = true

  try {
    await authAPI.changePassword({
      old_password: passwordForm.value.old_password,
      new_password: passwordForm.value.new_password,
      new_password_confirm: passwordForm.value.new_password_confirm
    })
    
    passwordSuccess.value = 'Password changed successfully!'
    passwordForm.value = {
      old_password: '',
      new_password: '',
      new_password_confirm: ''
    }
    
    setTimeout(() => {
      passwordSuccess.value = ''
    }, 3000)
    
  } catch (err) {
    console.error('Password change error:', err)
    if (err.response?.data) {
      const errors = err.response.data
      if (typeof errors === 'object') {
        const errorMessages = Object.values(errors).flat().join(', ')
        passwordError.value = errorMessages
      } else {
        passwordError.value = errors.message || 'Failed to change password'
      }
    } else {
      passwordError.value = 'Failed to change password'
    }
  } finally {
    isChangingPassword.value = false
  }
}

const updatePreferences = async () => {
  preferencesError.value = ''
  preferencesSuccess.value = ''
  isUpdatingPreferences.value = true

  try {
    // This would typically be an API call to update user preferences
    // Since there's no preference endpoint in your API, we'll simulate it
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    preferencesSuccess.value = 'Preferences updated successfully!'
    
    setTimeout(() => {
      preferencesSuccess.value = ''
    }, 3000)
    
  } catch (err) {
    preferencesError.value = 'Failed to update preferences'
  } finally {
    isUpdatingPreferences.value = false
  }
}

// Load user profile data
const loadProfile = async () => {
  try {
    const response = await authAPI.getProfile()
    const userData = response.data
    
    profileForm.value = {
      username: userData.username || '',
      email: userData.email || '',
      first_name: userData.first_name || '',
      last_name: userData.last_name || '',
      phone: userData.phone || '',
      date_of_birth: userData.date_of_birth || '',
      bio: userData.bio || ''
    }
  } catch (err) {
    console.error('Failed to load profile:', err)
  }
}

onMounted(() => {
  // Load current user data from store or API
  if (authStore.user) {
    profileForm.value = {
      username: authStore.user.username || '',
      email: authStore.user.email || '',
      first_name: authStore.user.first_name || '',
      last_name: authStore.user.last_name || '',
      phone: authStore.user.phone || '',
      date_of_birth: authStore.user.date_of_birth || '',
      bio: authStore.user.bio || ''
    }
  } else {
    // Load from API if not in store
    loadProfile()
  }
})
</script>