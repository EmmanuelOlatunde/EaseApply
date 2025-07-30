<template>
  <div class="min-h-screen bg-ash-50">
    <!-- Header -->
    <header class="bg-white border-b border-ash-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <div class="flex items-center">
            <h1 class="text-xl font-bold text-ash-800">EASEAPPLY AI</h1>
          </div>
          <nav class="flex items-center space-x-4">
            <template v-if="authStore.isAuthenticated">
              <router-link
                to="/dashboard"
                class="text-ash-600 hover:text-ash-800 px-3 py-2 rounded-md text-sm font-medium"
              >
                Dashboard
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
            </template>
            <template v-else>
              <button
                @click="showAuthModal = true"
                class="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors duration-200"
              >
                Sign In
              </button>
            </template>
          </nav>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <!-- Hero Section -->
      <div class="text-center mb-12">
        <h2 class="text-4xl font-bold text-ash-900 mb-4">
          Generate Professional Cover Letters with AI
        </h2>
        <p class="text-xl text-ash-600 max-w-2xl mx-auto">
          Upload your resume and job description to create personalized, compelling cover letters in seconds.
        </p>
      </div>

      <!-- Main Form -->
      <div class="bg-white rounded-lg shadow-sm border border-ash-200 p-8 mb-8">
        <form @submit.prevent="generateCoverLetter" class="space-y-8">
          <!-- Resume Upload -->
          <FileUpload
            label="Upload Your Resume"
            accept=".pdf"
            acceptText="PDF files only (max 10MB)"
            @file-selected="handleResumeUpload"
          />

          <!-- Job Description -->
          <div>
            <label class="block text-sm font-medium text-ash-700 mb-2">
              Job Description
            </label>
            <div class="relative">
              <textarea
                v-model="jobDescription"
                rows="8"
                class="w-full px-3 py-3 border border-ash-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                placeholder="Paste the complete job description here. Include requirements, responsibilities, and company information for the best results..."
                required
              ></textarea>
              <div class="absolute bottom-3 right-3 text-sm text-ash-500">
                {{ jobDescription.length }} characters
              </div>
            </div>
          </div>

          <!-- Additional Options -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-medium text-ash-700 mb-2">
                Tone (Optional)
              </label>
              <select
                v-model="tone"
                class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="professional">Professional</option>
                <option value="enthusiastic">Enthusiastic</option>
                <option value="confident">Confident</option>
                <option value="formal">Formal</option>
              </select>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-ash-700 mb-2">
                Length
              </label>
              <select
                v-model="length"
                class="w-full px-3 py-2 border border-ash-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="short">Short (200-300 words)</option>
                <option value="medium">Medium (300-400 words)</option>
                <option value="long">Long (400-500 words)</option>
              </select>
            </div>
          </div>

          <!-- Submit Button -->
          <div class="flex justify-center">
            <button
              type="submit"
              :disabled="!resumeFile || !jobDescription.trim() || isGenerating"
              class="px-8 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            >
              <span v-if="isGenerating" class="flex items-center">
                <div class="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                Generating Cover Letter...
              </span>
              <span v-else class="flex items-center">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Generate Cover Letter
              </span>
            </button>
          </div>
        </form>
      </div>

      <!-- Loading State -->
      <div v-if="isGenerating" class="bg-white rounded-lg shadow-sm border border-ash-200">
        <LoadingSpinner 
          message="Analyzing your resume and generating personalized cover letter..."
          :showProgress="true"
          :progress="progress"
        />
      </div>

      <!-- Cover Letter Output -->
      <CoverLetterOutput 
        v-if="generatedCoverLetter && !isGenerating"
        :coverLetter="generatedCoverLetter"
        :generatedAt="generatedAt"
      />

      <!-- Error State -->
      <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-6">
        <div class="flex items-center">
          <svg class="w-5 h-5 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 class="text-red-800 font-medium">Generation Failed</h3>
        </div>
        <p class="text-red-700 mt-2">{{ error }}</p>
        <button
          @click="error = null"
          class="mt-3 text-red-600 hover:text-red-500 text-sm font-medium"
        >
          Dismiss
        </button>
      </div>

      <!-- Tips Section -->
      <div class="mt-12 bg-blue-50 rounded-lg p-6">
        <h3 class="text-lg font-semibold text-blue-900 mb-4">Tips for Better Results</h3>
        <ul class="space-y-2 text-blue-800">
          <li class="flex items-start">
            <svg class="w-5 h-5 text-blue-600 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
            Ensure your resume is up-to-date and well-formatted
          </li>
          <li class="flex items-start">
            <svg class="w-5 h-5 text-blue-600 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
            Include the complete job description with requirements and company info
          </li>
          <li class="flex items-start">
            <svg class="w-5 h-5 text-blue-600 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
            Review and customize the generated letter before submitting
          </li>
        </ul>
      </div>
    </main>

    <!-- Auth Modal -->
    <AuthModal 
      :isOpen="showAuthModal"
      @close="showAuthModal = false"
      @success="handleAuthSuccess"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { analysisAPI } from '../services/api'
import FileUpload from '../components/FileUpload.vue'
import CoverLetterOutput from '../components/CoverLetterOutput.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import AuthModal from '../components/AuthModal.vue'

const authStore = useAuthStore()

// Form data
const resumeFile = ref(null)
const jobDescription = ref('')
const tone = ref('professional')
const length = ref('medium')

// State
const isGenerating = ref(false)
const progress = ref(0)
const generatedCoverLetter = ref('')
const generatedAt = ref(null)
const error = ref(null)
const showAuthModal = ref(false)

// Methods
const handleResumeUpload = (file) => {
  resumeFile.value = file
}

const generateCoverLetter = async () => {
  if (!resumeFile.value || !jobDescription.value.trim()) {
    error.value = 'Please upload a resume and provide a job description'
    return
  }

  isGenerating.value = true
  error.value = null
  progress.value = 0

  // Simulate progress
  const progressInterval = setInterval(() => {
    if (progress.value < 90) {
      progress.value += Math.random() * 10
    }
  }, 500)

  try {
    const formData = new FormData()
    formData.append('resume', resumeFile.value)
    formData.append('job_description', jobDescription.value)
    formData.append('tone', tone.value)
    formData.append('length', length.value)

    const response = await analysisAPI.generateCoverLetter(formData)
    
    clearInterval(progressInterval)
    progress.value = 100

    setTimeout(() => {
      generatedCoverLetter.value = response.data.cover_letter
      generatedAt.value = new Date()
      isGenerating.value = false
    }, 500)

  } catch (err) {
    clearInterval(progressInterval)
    isGenerating.value = false
    error.value = err.response?.data?.message || 'Failed to generate cover letter. Please try again.'
  }
}

const handleAuthSuccess = () => {
  showAuthModal.value = false
}

const handleLogout = async () => {
  await authStore.logout()
}

onMounted(() => {
  // Any initialization code
})
</script>