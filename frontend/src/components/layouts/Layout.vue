<template>
  <!-- Full lebar & tinggi -->
  <div class="flex h-screen w-screen">

    <!-- Konten: 80% -->
    <main class="w-full h-full bg-gray-100 overflow-y-auto p-6">
      <router-view />
    </main>
  </div>
</template>

<script setup>
// import Sidebar from '@/components/Sidebar.vue'
import Sidebar from './Sidebar.vue'
</script>
