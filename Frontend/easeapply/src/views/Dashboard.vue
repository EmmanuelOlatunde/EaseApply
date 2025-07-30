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
              to="/profile"
              class="text-ash-600 hover:text-ash-800 px-3 py-2 rounded-md text-sm font-medium"
            >
              Profile
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
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Welcome Section -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-ash-900">
          Welcome back, {{ authStore.user?.full_name || 'User' }}!
        </h1>
        <p class="text-ash-600 mt-2">Here's an overview of your cover letter generation activity.</p>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow-sm border border-ash-200 p-6">
          <div class="flex items-center">
            <div class="p-2 bg-blue-100 rounded-lg">
              <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-ash-600">Cover Letters Generated</p>
              <p class="text-2xl font-bold text-ash-900">{{ stats.totalGenerated }}</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg shadow-sm border border-ash-200 p-6">
          <div class="flex items-center">
            <div class="p-2 bg-green-100 rounded-lg">
              <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3a4 4 0 118 0v4m-4 8a3 3 0 01-3-3V8a3 3 0 016 0v4a3 3 0 01-3 3z" />
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-ash-600">This Month</p>
              <p class="text-2xl font-bold text-ash-900">{{ stats.thisMonth }}</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg shadow-sm border border-ash-200 p-6">
          <div class="flex items-center">
            <div class="p-2 bg-purple-100 rounded-lg">
              <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-ash-600">Success Rate</p>
              <p class="text-2xl font-bold text-ash-900">{{ stats.successRate }}%</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="bg-white rounded-lg shadow-sm border border-ash-200">
        <div class="p-6 border-b border-ash-200">
          <h2 class="text-lg font-semibold text-ash-800">Recent Cover Letters</h2>
        </div>
        
        <div v-if="recentLetters.length === 0" class="p-6 text-center">
          <svg class="mx-auto h-12 w-12 text-ash-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p class="mt-4 text-ash-600">No cover letters generated yet.</p>
          <router-link
            to="/"
            class="mt-2 inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors duration-200"
          >
            Generate Your First Cover Letter
          </router-link>
        </div>
        
        <div v-else class="divide-y divide-ash-200">
          <div
            v-for="letter in recentLetters"
            :key="letter.id"
            class="p-6 hover:bg-ash-50 transition-colors duration-200"
          >
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <h3 class="text-sm font-medium text-ash-900">{{ letter.jobTitle }}</h3>
                <p class="text-sm text-ash-600 mt-1">{{ letter.company }}</p>
                <p class="text-xs text-ash-500 mt-2">Generated {{ formatDate(letter.createdAt) }}</p>
              </div>
              <div class="flex items-center space-x-2">
                <span
                  class="px-2 py-1 text-xs font-medium rounded-full"
                  :class="{
                    'bg-green-100 text-green-800': letter.status === 'completed',
                    'bg-yellow-100 text-yellow-800': letter.status === 'pending',
                    'bg-red-100 text-red-800': letter.status === 'failed'
                  }"
                >
                  {{ letter.status }}
                </span>
                <button
                  @click="viewLetter(letter)"
                  class="text-blue-600 hover:text-blue-500 text-sm font-medium"
                >
                  View
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="bg-white rounded-lg shadow-sm border border-ash-200 p-6">
          <h3 class="text-lg font-medium text-ash-900 mb-4">Quick Actions</h3>
          <div class="space-y-3">
            <router-link
              to="/"
              class="flex items-center p-3 text-sm text-ash-700 rounded-lg hover:bg-ash-50 transition-colors duration-200"
            >
              <svg class="w-5 h-5 mr-3 text-ash-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Create New Cover Letter
            </router-link>
            <router-link
              to="/profile"
              class="flex items-center p-3 text-sm text-ash-700 rounded-lg hover:bg-ash-50 transition-colors duration-200"
            >
              <svg class="w-5 h-5 mr-3 text-ash-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              Update Profile
            </router-link>
          </div>
        </div>

        <div class="bg-white rounded-lg shadow-sm border border-ash-200 p-6">
          <h3 class="text-lg font-medium text-ash-900 mb-4">Tips & Resources</h3>
          <div class="space-y-3 text-sm text-ash-600">
            <p>• Keep your resume updated for better results</p>
            <p>• Customize each cover letter for specific roles</p>
            <p>• Review AI suggestions before submitting</p>
            <p>• Use different tones for different industries</p>
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

const authStore = useAuthStore()
const router = useRouter()

const stats = ref({
  totalGenerated: 0,
  thisMonth: 0,
  successRate: 0
})

const recentLetters = ref([])

const handleLogout = async () => {
  await authStore.logout()
  router.push('/')
}

const formatDate = (date) => {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  }).format(new Date(date))
}

const viewLetter = (letter) => {
  // Implement view letter functionality
  console.log('View letter:', letter)
}

onMounted(() => {
  // Load dashboard data
  // This would typically come from your API
  stats.value = {
    totalGenerated: 12,
    thisMonth: 5,
    successRate: 95
  }

  recentLetters.value = [
    {
      id: 1,
      jobTitle: 'Senior Frontend Developer',
      company: 'Tech Corp',
      status: 'completed',
      createdAt: '2024-01-15'
    },
    {
      id: 2,
      jobTitle: 'Product Manager',
      company: 'StartupXYZ',
      status: 'completed',
      createdAt: '2024-01-12'
    },
    {
      id: 3,
      jobTitle: 'UX Designer',
      company: 'Design Studio',
      status: 'completed',
      createdAt: '2024-01-10'
    }
  ]
})
</script>