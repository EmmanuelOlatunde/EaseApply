<template>
  <div id="app">
    <router-view />

    <!-- ✅ Toast Notification -->
    <transition name="fade">
      <div
        v-if="toast.show"
        class="fixed bottom-4 right-4 px-4 py-3 rounded-lg shadow-lg text-white z-50"
        :class="{
          'bg-green-600': toast.type === 'success',
          'bg-red-600': toast.type === 'error',
          'bg-yellow-500': toast.type === 'warning'
        }"
      >
        {{ toast.message }}
      </div>
    </transition>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import { toast } from './api'  // ✅ import your reactive toast here
import { useRoute } from 'vue-router'
import { showToast } from './api'

const authStore = useAuthStore()
const route = useRoute()

onMounted(() => {
  if (authStore.token) {
    console.log('User is already authenticated')
  }

  const status = route.query.status
  if (status === 'success') {
    showToast('✅ Email verified successfully!', 'success', 10000)
  } else if (status === 'invalid') {
    showToast('❌ Invalid verification link.', 'error', 10000)
  } else if (status === 'expired') {
    showToast('⚠️ Verification link expired.', 'warning', 10000)
  }
})
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
