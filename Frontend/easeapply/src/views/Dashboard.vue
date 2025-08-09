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
              :disabled="isLoading"
            >
              Logout
            </button>
          </nav>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Loading State -->
      <div v-if="isLoading" class="flex justify-center items-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>

      <div v-else>
        <!-- Welcome Section -->
        <div class="mb-8">
          <h1 class="text-3xl font-bold text-ash-900">
            Welcome back, {{ authStore.user?.username || 'User' }}!
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
                <p class="text-sm font-medium text-ash-600">Job Descriptions</p>
                <p class="text-2xl font-bold text-ash-900">{{ stats.totalJobs }}</p>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-lg shadow-sm border border-ash-200 p-6">
            <div class="flex items-center">
              <div class="p-2 bg-green-100 rounded-lg">
                <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div class="ml-4">
                <p class="text-sm font-medium text-ash-600">Resumes Uploaded</p>
                <p class="text-2xl font-bold text-ash-900">{{ stats.totalResumes }}</p>
              </div>
            </div>
          </div>

          <!-- <div class="bg-white rounded-lg shadow-sm border border-ash-200 p-6">
            <div class="flex items-center">
              <div class="p-2 bg-purple-100 rounded-lg">
                <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div class="ml-4">
                <p class="text-sm font-medium text-ash-600">Processed Jobs</p>
                <p class="text-2xl font-bold text-ash-900">{{ stats.processedJobs }}</p>
              </div>
            </div>
          </div> -->
        </div>

        <!-- Recent Activity -->
        <div class="bg-white rounded-lg shadow-sm border border-ash-200">
          <div class="p-6 border-b border-ash-200">
            <h2 class="text-lg font-semibold text-ash-800">Recent Job Descriptions</h2>
          </div>
          
          <div v-if="recentJobs.length === 0" class="p-6 text-center">
            <svg class="mx-auto h-12 w-12 text-ash-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p class="mt-4 text-ash-600">No job descriptions added yet.</p>
            <router-link
              to="/"
              class="mt-2 inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors duration-200"
            >
              Add Your First Job Description
            </router-link>
          </div>
          
          <div v-else class="divide-y divide-ash-200">
            <div
              v-for="job in recentJobs"
              :key="job.id"
              class="p-6 hover:bg-ash-50 transition-colors duration-200"
            >
              <div class="flex items-center justify-between">
                <div class="flex-1">
                  <h3 class="text-sm font-medium text-ash-900">{{ job.title || 'Untitled Position' }}</h3>
                  <p class="text-sm text-ash-600 mt-1">{{ job.company || 'Company not specified' }}</p>
                  <p class="text-xs text-ash-500 mt-2">Added {{ formatDate(job.created_at) }}</p>
                </div>
                <div class="flex items-center space-x-2">
                  <span
                    class="px-2 py-1 text-xs font-medium rounded-full"
                    :class="{
                      'bg-green-100 text-green-800': job.is_processed,
                      'bg-yellow-100 text-yellow-800': !job.is_processed
                    }"
                  >
                    {{ job.is_processed ? 'Processed' : 'Pending' }}
                  </span>
                  <button
                    @click="viewJob(job)"
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
                Generate Cover Letter
              </router-link>
              <router-link
                to="/resumes"
                class="flex items-center p-3 text-sm text-ash-700 rounded-lg hover:bg-ash-50 transition-colors duration-200"
              >
                <svg class="w-5 h-5 mr-3 text-ash-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                Upload Resume
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
            <h3 class="text-lg font-medium text-ash-900 mb-4">Recent Resumes</h3>
            <div v-if="recentResumes.length === 0" class="text-sm text-ash-600">
              <p>No resumes uploaded yet.</p>
            </div>
            <div v-else class="space-y-3">
              <div
                v-for="resume in recentResumes.slice(0, 3)"
                :key="resume.id"
                class="flex items-center justify-between p-2 rounded-lg hover:bg-ash-50"
              >
                <div class="flex-1">
                  <p class="text-sm font-medium text-ash-900">{{ resume.original_filename }}</p>
                  <p class="text-xs text-ash-500">{{ formatDate(resume.uploaded_at) }}</p>
                </div>
                <span
                  class="text-xs px-2 py-1 rounded-full"
                  :class="{
                    'bg-green-100 text-green-800': resume.is_parsed,
                    'bg-yellow-100 text-yellow-800': !resume.is_parsed
                  }"
                >
                  {{ resume.is_parsed ? 'Parsed' : 'Processing' }}
                </span>
              </div>
            </div>
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
import { jobAPI, resumeAPI } from '../services/api'

const authStore = useAuthStore()
const router = useRouter()

const isLoading = ref(true)
const stats = ref({
  totalJobs: 0,
  totalResumes: 0,
  processedJobs: 0
})

const recentJobs = ref([])
const recentResumes = ref([])

const handleLogout = async () => {
  try {
    await authStore.logout()
    router.push('/')
  } catch (error) {
    console.error('Logout error:', error)
  }
}

const formatDate = (date) => {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  }).format(new Date(date))
}

const viewJob = (job) => {
  router.push(`/jobs/${job.id}`)
}

const loadDashboardData = async () => {
  try {
    isLoading.value = true
    
    // Initialize auth if user data is not loaded
    if (!authStore.user && authStore.token) {
      await authStore.initializeAuth()
    }
    
    // Load jobs and resumes concurrently
    const [jobsResponse, resumesResponse] = await Promise.all([
      jobAPI.list(1),
      resumeAPI.list(1)
    ])

    const jobs = jobsResponse.data.results || []
    const resumes = resumesResponse.data.results || []

    // Update stats
    stats.value = {
      totalJobs: jobsResponse.data.count || 0,
      totalResumes: resumesResponse.data.count || 0,
      processedJobs: jobs.filter(job => job.is_processed).length
    }

    // Set recent data (limit to 5 most recent)
    recentJobs.value = jobs.slice(0, 5)
    recentResumes.value = resumes.slice(0, 3)

  } catch (error) {
    console.error('Error loading dashboard data:', error)
    // Handle specific error cases
    if (error.response?.status === 401) {
      await authStore.logout()
      router.push('/')
    }
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>