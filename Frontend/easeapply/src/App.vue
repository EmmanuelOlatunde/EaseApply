<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()


onMounted(() => {
  if (authStore.token) {
    console.log('User is already authenticated')
  }

  checkStatus(route.query.status)
})

</script>
