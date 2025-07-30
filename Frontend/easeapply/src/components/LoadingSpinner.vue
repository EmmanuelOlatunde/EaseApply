<template>
  <div class="flex flex-col items-center justify-center p-8">
    <div class="relative">
      <div class="w-12 h-12 border-4 border-ash-200 border-t-blue-600 rounded-full animate-spin"></div>
    </div>
    <p class="mt-4 text-ash-600 text-sm">{{ message }}</p>
    <div v-if="showProgress" class="mt-2 w-64 bg-ash-200 rounded-full h-2">
      <div 
        class="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
        :style="{ width: `${progress}%` }"
      ></div>
    </div>
  </div>
</template>

<script setup>
// Props are automatically available when using defineProps

defineProps({
  message: {
    type: String,
    default: 'Processing your request...'
  },
  showProgress: {
    type: Boolean,
    default: false
  },
  progress: {
    type: Number,
    default: 0
  }
})
</script>