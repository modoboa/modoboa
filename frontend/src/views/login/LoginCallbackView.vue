<script setup lang="js">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores'
const authStore = useAuthStore()

onMounted(() => {
  authStore.completeLogin()
})
</script>

<template>
</template>
