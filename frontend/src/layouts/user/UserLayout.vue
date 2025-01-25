<template>
  <ConnectedLayout :menu-items="layoutStore.leftMenuItems" />
</template>

<script setup>
import { useLayoutStore } from '@/stores'
import ConnectedLayout from '@/layouts/connected/ConnectedLayout.vue'

const layoutStore = useLayoutStore()
</script>
