<template>
  <div class="min-h-screen flex flex-col items-center justify-center bg-gray-50 text-center p-6">
    <h1 class="text-6xl font-bold text-gray-800">404</h1>
    <p class="mt-4 text-lg text-gray-600">Oops! The page you’re looking for doesn’t exist.</p>
    
    <router-link 
      to="/" 
      class="mt-6 inline-block px-6 py-3 bg-blue-600 text-white text-sm font-medium rounded-lg shadow hover:bg-blue-500 transition"
    >
      Go back home
    </router-link>
  </div>
</template>

<script setup>
// No script needed for this simple 404 page
</script>

<style scoped>
/* You can tweak styling or remove if you're using Tailwind */
</style>
