<template>
  <ComposeEmailForm
    :original-email="email"
    :reply-all="route.query.all === 'true'"
    @on-toggle-html-mode="getEmailContent"
  />
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import ComposeEmailForm from '@/components/webmail/ComposeEmailForm'
import api from '@/api/webmail'

const route = useRoute()

const email = ref()

const getEmailContent = (html) => {
  email.value = ''
  api
    .getEmailContent(route.query.mailbox, route.query.mailid, {
      context: 'reply',
      dformat: html ? 'html' : 'plain',
    })
    .then((resp) => {
      email.value = resp.data
    })
}

getEmailContent()
</script>
