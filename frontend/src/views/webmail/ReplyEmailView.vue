<template>
  <ComposeEmailForm
    v-if="email"
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

// Refetch the quoted body when the editor format changes. Do NOT null the
// email first: v-if would unmount/remount ComposeEmailForm and reset its
// html-mode state, leaving the HTML body in the plain-text textarea.
const getEmailContent = (html) => {
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
