<template>
  <ComposeEmailForm
    v-if="email"
    :original-email="email"
    forward
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

// Same contract as the reply flow: fetch the quoted body in the format the
// editor is in, and refetch when the user toggles plain/HTML. Do NOT null the
// email first — v-if would remount ComposeEmailForm and reset its html-mode.
const getEmailContent = (html) => {
  api
    .getEmailContent(route.query.mailbox, route.query.mailid, {
      context: 'forward',
      dformat: html ? 'html' : 'plain',
    })
    .then((resp) => {
      email.value = resp.data
    })
}

getEmailContent()
</script>
