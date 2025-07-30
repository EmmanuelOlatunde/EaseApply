<template>
  <div v-if="coverLetter" class="w-full bg-white border border-ash-200 rounded-lg shadow-sm slide-up">
    <div class="p-6 border-b border-ash-200">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-ash-800">Generated Cover Letter</h3>
        <div class="flex space-x-3">
          <button
            @click="copyToClipboard"
            class="inline-flex items-center px-3 py-2 text-sm font-medium text-ash-700 bg-ash-100 rounded-md hover:bg-ash-200 transition-colors duration-200"
          >
            <svg v-if="!copied" class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <svg v-else class="w-4 h-4 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            {{ copied ? 'Copied!' : 'Copy' }}
          </button>
          
          <button
            @click="downloadCoverLetter"
            class="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors duration-200"
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Download
          </button>
        </div>
      </div>
    </div>
    
    <div class="p-6">
      <div 
        ref="coverLetterContent"
        class="prose prose-ash max-w-none bg-ash-50 rounded-lg p-6 whitespace-pre-wrap text-sm leading-relaxed text-ash-800"
        style="font-family: 'Times New Roman', serif; line-height: 1.6;"
      >
        {{ coverLetter }}
      </div>
    </div>
    
    <div class="px-6 pb-6">
      <div class="flex items-center justify-between text-sm text-ash-500">
        <span>Generated on {{ formatDate(generatedAt) }}</span>
        <span>{{ wordCount }} words</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  coverLetter: {
    type: String,
    required: true
  },
  generatedAt: {
    type: Date,
    default: () => new Date()
  }
})

const coverLetterContent = ref(null)
const copied = ref(false)

const wordCount = computed(() => {
  return props.coverLetter.trim().split(/\s+/).length
})

const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(props.coverLetter)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy:', err)
    // Fallback for older browsers
    const textArea = document.createElement('textarea')
    textArea.value = props.coverLetter
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  }
}

const downloadCoverLetter = () => {
  const blob = new Blob([props.coverLetter], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `cover-letter-${new Date().toISOString().split('T')[0]}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const formatDate = (date) => {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}
</script>