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
              <li>
                <button
                  @click="activeTab = 'preferences'"
                  class="w-full text-left px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200"
                  :class="activeTab === 'preferences' ? 'bg-blue-100 text-blue-700' : 'text-ash-600 hover:text-ash-800 hover:bg-ash-50'"
                >
                  Preferences
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
                  <label class="block text-sm font-medium text-ash-700 mb-2">Full Name</label>
                  <input
                    v-model="profileForm.fullName"
                    type="text"
                    class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter your full name"
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-ash-700 mb-2">Email</label>
                  <input
                    v-model="profileForm.email"
                    type="email"
                    class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter your email"
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
                <label class="block text-sm font-medium text-ash-700 mb-2">Professional Title</label>
                <input
                  v-model="profileForm.title"
                  type="text"
                  class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., Senior Software Engineer"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-ash-700 mb-2">Industry</label>
                <select
                  v-model="profileForm.industry"
                  class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select Industry</option>
                  <option value="technology">Technology</option>
                  <option value="finance">Finance</option>
                  <option value="healthcare">Healthcare</option>
                  <option value="education">Education</option>
                  <option value="marketing">Marketing</option>
                  <option value="consulting">Consulting</option>
                  <option value="other">Other</option>
                </select>
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
                  v-model="passwordForm.currentPassword"
                  type="password"
                  class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter current password"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-ash-700 mb-2">New Password</label>
                <input
                  v-model="passwordForm.newPassword"
                  type="password"
                  class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter new password"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-ash-700 mb-2">Confirm New Password</label>
                <input
                  v-model="passwordForm.confirmPassword"
                  type="password"
                  class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Confirm new password"
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

          <!-- Preferences -->
          <div v-if="activeTab === 'preferences'" class="bg-white rounded-lg shadow-sm border border-ash-200 p-6">
            <h2 class="text-lg font-semibold text-ash-800 mb-6">Preferences</h2>
            
            <form @submit.prevent="updatePreferences" class="space-y-6">
              <div>
                <label class="block text-sm font-medium text-ash-700 mb-4">Default Cover Letter Settings</label>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label class="block text-sm font-medium text-ash-600 mb-2">Default Tone</label>
                    <select
                      v-model="preferencesForm.defaultTone"
                      class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="professional">Professional</option>
                      <option value="enthusiastic">Enthusiastic</option>
                      <option value="confident">Confident</option>
                      <option value="formal">Formal</option>
                    </select>
                  </div>
                  
                  <div>
                    <label class="block text-sm font-medium text-ash-600 mb-2">Default Length</label>
                    <select
                      v-model="preferencesForm.defaultLength"
                      class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="short">Short (200-300 words)</option>
                      <option value="medium">Medium (300-400 words)</option>
                      <option value="long">Long (400-500 words)</option>
                    </select>
                  </div>
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-ash-700 mb-4">Email Notifications</label>
                <div class="space-y-3">
                  <label class="flex items-center">
                    <input
                      v-model="preferencesForm.emailNotifications.generation"
                      type="checkbox"
                      class="rounded border-ash-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span class="ml-2 text-sm text-ash-700">Notify when cover letter generation is complete</span>
                  </label>
                  
                  <label class="flex items-center">
                    <input
                      v-model="preferencesForm.emailNotifications.tips"
                      type="checkbox"
                      class="rounded border-ash-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span class="ml-2 text-sm text-ash-700">Receive weekly job search tips</span>
                  </label>
                </div>
              </div>

              <div v-if="preferencesError" class="text-red-600 text-sm">{{ preferencesError }}</div>
              <div v-if="preferencesSuccess" class="text-green-600 text-sm">{{ preferencesSuccess }}</div>

              <div class="flex justify-end">
                <button
                  type="submit"
                  :disabled="isUpdatingPreferences"
                  class="px-6 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span v-if="isUpdatingPreferences">Updating...</span>
                  <span v-else>Update Preferences</span>
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

// Profile form
const profileForm = ref({
  fullName: '',
  email: '',
  phone: '',
  title: '',
  industry: ''
})

const isUpdatingProfile = ref(false)
const profileError = ref('')
const profileSuccess = ref('')

// Password form
const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
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
    await authStore.updateProfile({
      full_name: profileForm.value.fullName,
      email: profileForm.value.email,
      phone: profileForm.value.phone,
      title: profileForm.value.title,
      industry: profileForm.value.industry
    })
    
    profileSuccess.value = 'Profile updated successfully!'
    
    setTimeout(() => {
      profileSuccess.value = ''
    }, 3000)
    
  } catch (err) {
    profileError.value = err.response?.data?.message || 'Failed to update profile'
  } finally {
    isUpdatingProfile.value = false
  }
}

const changePassword = async () => {
  passwordError.value = ''
  passwordSuccess.value = ''

  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    passwordError.value = 'New passwords do not match'
    return
  }

  if (passwordForm.value.newPassword.length < 8) {
    passwordError.value = 'New password must be at least 8 characters long'
    return
  }

  isChangingPassword.value = true

  try {
    await authAPI.changePassword({
      old_password: passwordForm.value.currentPassword,
      new_password: passwordForm.value.newPassword
    })
    
    passwordSuccess.value = 'Password changed successfully!'
    passwordForm.value = {
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    }
    
    setTimeout(() => {
      passwordSuccess.value = ''
    }, 3000)
    
  } catch (err) {
    passwordError.value = err.response?.data?.message || 'Failed to change password'
  } finally {
    isChangingPassword.value = false
  }
}

const updatePreferences = async () => {
  preferencesError.value = ''
  preferencesSuccess.value = ''
  isUpdatingPreferences.value = true

  try {
    // This would typically be an API call
    // await api.updatePreferences(preferencesForm.value)
    
    // For now, just simulate success
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

onMounted(() => {
  // Load current user data
  if (authStore.user) {
    profileForm.value = {
      fullName: authStore.user.full_name || '',
      email: authStore.user.email || '',
      phone: authStore.user.phone || '',
      title: authStore.user.title || '',
      industry: authStore.user.industry || ''
    }
  }
})
</script>