<template>
  <v-card class="mt-6 mb-2">
    <v-toolbar color="white" flat>
      <v-checkbox class="mr-4" hide-details />

      <v-text-field
        v-model="search"
        prepend-inner-icon="mdi-magnify"
        :placeholder="$gettext('Search')"
        variant="outlined"
        single-line
        flat
        hide-details
        density="compact"
        class="flex-grow-0 w-33 mr-4"
      ></v-text-field>
    </v-toolbar>
  </v-card>
  <v-skeleton-loader v-if="loading" type="card@2"></v-skeleton-loader>
  <template v-else>
    <v-card
      v-for="email in emails"
      :key="email.imapid"
      density="compact"
      class="mb-2"
    >
      <v-card-text
        class="d-flex align-center"
        :class="{ 'font-weight-bold': email.style === 'unseen' }"
      >
        <v-checkbox :value="email.imapid" hide-details />
        <v-btn
          :icon="email.flagged ? 'mdiu-star' : 'mdi-star-outline'"
          variant="flat"
        />
        <div class="ml-4 clickable" @click="openEmail(email.imapid)">
          <div>{{ email.subject }}</div>
          <div class="mt-1 text-grey">
            <span
              v-if="email.from_address.name"
              :title="email.from_address.address"
              >{{ email.from_address.name }}</span
            >
            <span v-else>{{ email.from_address.address }}</span>
          </div>
        </div>
        <v-spacer />
        <div class="text-right">
          <div>{{ email.date }}</div>
          <div class="mt-1">
            <v-icon v-if="email.answered" icon="mdi-reply-outline" />
            <v-icon v-if="email.forwarded" icon="mdi-share-outline" />
            <v-icon v-if="email.attachments" icon="mdi-paperclip" />
            <span class="text-grey">{{ $filesize(email.size) }}</span>
          </div>
        </div>
      </v-card-text>
    </v-card>
  </template>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/webmail'

const props = defineProps({
  mailbox: {
    type: String,
    default: 'INBOX',
  },
})

const router = useRouter()

const loading = ref(false)
const emails = ref([])
const search = ref('')

const openEmail = (emailid) => {
  router.push({
    name: 'EmailView',
    query: { mailbox: props.mailbox, mailid: emailid },
  })
}

watch(
  () => props.mailbox,
  (value) => {
    emails.value = []
    loading.value = true
    api
      .getMailboxEmails(value, {})
      .then((resp) => {
        emails.value = resp.data
        loading.value = false
      })
      .catch(() => {
        loading.value = false
      })
  },
  { immediate: true }
)
</script>

<style lang="scss" scoped>
.v-card-text {
  padding: 0;
}
.clickable {
  cursor: pointer;
}
</style>
