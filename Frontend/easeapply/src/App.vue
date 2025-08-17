<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import { useRoute } from 'vue-router'
import { showToast } from './utils/toast' // adjust this path if needed

const authStore = useAuthStore()
const route = useRoute()

onMounted(() => {
  // Initialize app - check if user is already logged in
  if (authStore.token) {
    console.log('User is already authenticated')
  }

  // Check for email verification status in query params
  const status = route.query.status
  if (status === 'success') {
    showToast('✅ Email verified successfully!')
  } else if (status === 'invalid') {
    showToast('❌ Invalid verification link.')
  } else if (status === 'expired') {
    showToast('⚠️ Verification link expired.')
  }
})
</script>

<style>
/* Global styles are imported in main.js */
</style>
