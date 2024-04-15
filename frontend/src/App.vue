<template>
  <router-view />
</template>

<script setup>
import { useAuthStore } from '@/stores'

const authStore = useAuthStore()

authStore.initialize()
</script>
