<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { useAuthStore } from './stores/auth'
import { useRoute } from 'vue-router'
import { showToast } from './api'

const authStore = useAuthStore()
const route = useRoute()

onMounted(() => {
  if (authStore.token) {
    console.log('User is already authenticated')
  }

  checkStatus(route.query.status)
})

watch(
  () => route.query.status,
  (newStatus) => {
    checkStatus(newStatus)
  },
  { immediate: true }
)

function checkStatus(status) {
  if (status === 'success') {
    showToast('✅ Email verified successfully!')
  } else if (status === 'invalid') {
    showToast('❌ Invalid verification link.', 'error')
  } else if (status === 'expired') {
    showToast('⚠️ Verification link expired.', 'warning')
  }
}
</script>
