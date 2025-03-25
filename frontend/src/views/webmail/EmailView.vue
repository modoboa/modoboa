<template>
  <v-toolbar color="white" class="mt-12">
    <v-btn variant="tonal" @click="close">
      <v-icon icon="mdi-arrow-left" />
      {{ $gettext('Back') }}
    </v-btn>
    <v-btn color="primary">
      {{ $gettext('Reply') }}
    </v-btn>
  </v-toolbar>

  <div v-if="email" class="mt-4">
    <h3>{{ email.subject }}</h3>
    <div>{{ email.from_address.name }}</div>
    <iframe class="email-frame" />
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api/webmail'

const route = useRoute()

const email = ref(null)

onMounted(() => {
  api.getEmailContent(route.query.mailbox, route.query.mailid).then((resp) => {
    email.value = resp.data
    nextTick(() => {
      const iframe = document.createElement('iframe')
      iframe.classList.add('email-frame')
      document.querySelector('iframe').replaceWith(iframe)
      const iframeDoc = iframe.contentDocument
      iframeDoc.write(email.value.body)
      iframeDoc.close()
    })
  })
})
</script>

<style>
.email-frame {
  width: 100%;
  min-height: 1000px;
  border: none;
  margin-top: 10px;
}
</style>
