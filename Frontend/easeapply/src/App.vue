<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()

onMounted(() => {
  // Initialize app - check if user is already logged in
  if (authStore.token) {
    // You could validate the token here or fetch user data
    console.log('User is already authenticated')
  }
})
</script>

<style>
/* Global styles are imported in main.js */
</style>