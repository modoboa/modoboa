<template>
  <ComposeEmailForm :original-email="email" />
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import ComposeEmailForm from '@/components/webmail/ComposeEmailForm'
import api from '@/api/webmail'

const route = useRoute()

const email = ref()

api
  .getEmailContent(route.query.mailbox, route.query.mailid, {
    context: 'forward',
  })
  .then((resp) => {
    email.value = resp.data
  })
</script>
