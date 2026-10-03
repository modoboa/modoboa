<template>
  <ComposeEmailForm reply :reply-all="route.query.all === 'true'" />
</template>

<script setup>
import { useRoute } from 'vue-router'
import ComposeEmailForm from '@/components/webmail/ComposeEmailForm'

const route = useRoute()
</script>
