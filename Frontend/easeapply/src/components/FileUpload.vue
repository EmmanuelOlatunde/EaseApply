<template>
  <div class="w-full">
    <label class="block text-sm font-medium text-ash-700 mb-2">
      {{ label }}
    </label>
    <div
      @drop="handleDrop"
      @dragover.prevent
      @dragenter.prevent
      class="relative border-2 border-dashed border-ash-300 rounded-lg p-6 text-center hover:border-ash-400 transition-colors duration-200"
      :class="{ 'border-blue-400 bg-blue-50': isDragging }"
    >
      <input
        ref="fileInput"
        type="file"
        :accept="accept"
        @change="handleFileSelect"
        class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        :disabled="disabled"
      />
      
      <div v-if="!selectedFile" class="space-y-2">
        <svg class="mx-auto h-12 w-12 text-ash-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
          <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <div>
          <p class="text-ash-600">
            <span class="text-blue-600 hover:text-blue-500 cursor-pointer">Click to upload</span>
            or drag and drop
          </p>
          <p class="text-sm text-ash-500">{{ acceptText }}</p>
        </div>
      </div>
      
      <div v-else class="space-y-2">
        <svg class="mx-auto h-12 w-12 text-green-500" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
        </svg>
        <p class="text-ash-700 font-medium">{{ selectedFile.name }}</p>
        <p class="text-sm text-ash-500">{{ formatFileSize(selectedFile.size) }}</p>
        <button
          @click="removeFile"
          type="button"
          class="text-red-600 hover:text-red-500 text-sm font-medium"
        >
          Remove file
        </button>
      </div>
    </div>
    
    <p v-if="error" class="mt-2 text-sm text-red-600">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  label: {
    type: String,
    default: 'Upload file'
  },
  accept: {
    type: String,
    default: '.pdf,.docx'
  },
  acceptText: {
    type: String,
    default: 'PDF files only'
  },
  maxSize: {
    type: Number,
    default: 10 * 1024 * 1024 // 10MB
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['file-selected'])

const fileInput = ref(null)
const selectedFile = ref(null)
const error = ref(null)
const isDragging = ref(false)

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  validateAndSetFile(file)
}

const handleDrop = (event) => {
  event.preventDefault()
  isDragging.value = false
  const file = event.dataTransfer.files[0]
  validateAndSetFile(file)
}

const validateAndSetFile = (file) => {
  error.value = null
  
  if (!file) return
  
  // Validate file type
  const allowedExtensions = ['.pdf', '.docx']
  const fileName = file.name.toLowerCase()
  const isValidType = allowedExtensions.some(ext => fileName.endsWith(ext))

  if (!isValidType) {
    error.value = 'Please select a PDF or DOCX file'
    return
  }

  
  // Validate file size
  if (file.size > props.maxSize) {
    error.value = `File size must be less than ${formatFileSize(props.maxSize)}`
    return
  }
  
  selectedFile.value = file
  emit('file-selected', file)
}

const removeFile = () => {
  selectedFile.value = null
  error.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
  emit('file-selected', null)
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
</script>