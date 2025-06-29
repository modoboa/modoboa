<template>
  <v-card class="mt-6 mb-2 mx-1">
    <v-toolbar color="white" flat>
      <v-checkbox
        v-model="selectAll"
        class="mr-4"
        hide-details
        @update:model-value="toggleAllSelection"
      />

      <v-text-field
        v-model="search"
        prepend-inner-icon="mdi-magnify"
        :placeholder="$gettext('Search in messages')"
        variant="outlined"
        single-line
        flat
        hide-details
        density="compact"
        class="flex-grow-0 w-33 mr-4"
        clearable
        @click:clear="fetchEmails"
        @keyup.enter="submitSearch"
      ></v-text-field>
      <v-btn
        class="ml-2"
        color="error"
        variant="tonal"
        icon="mdi-trash-can"
        size="small"
        :loading="working"
        @click="deleteSelection"
      >
      </v-btn>
      <v-btn
        v-if="$route.params.mailbox !== 'Junk'"
        class="ml-2"
        color="warning"
        variant="tonal"
        icon="mdi-fire"
        size="small"
        :loading="working"
        @click="markSelectionAsJunk"
      >
      </v-btn>
      <v-btn
        v-else
        class="ml-2"
        color="success"
        variant="tonal"
        icon="mdi-thumb-up"
        size="small"
        :loading="working"
        @click="markSelectionAsNotJunk"
      >
      </v-btn>
      <v-btn class="ml-2" variant="tonal" icon size="small">
        <v-icon icon="mdi-cog" />
        <v-menu activator="parent">
          <v-list density="compact">
            <v-list-item
              :title="$gettext('Mark as read')"
              prepend-icon="mdi-eye"
              @click="() => flagSelection('read')"
            />
            <v-list-item
              :title="$gettext('Mark as unread')"
              prepend-icon="mdi-eye-outline"
              @click="() => flagSelection('unread')"
            />
            <v-list-item
              :title="$gettext('Mark as followed')"
              prepend-icon="mdi-star"
              @click="() => flagSelection('flagged')"
            />
            <v-list-item
              :title="$gettext('Mark as unfollowed')"
              prepend-icon="mdi-star-outline"
              @click="() => flagSelection('unflagged')"
            />
            <v-list-item
              v-if="$route.params.mailbox !== 'Trash'"
              :title="$gettext('Empty mailbox')"
              prepend-icon="mdi-trash-can"
              @click="emptyMailbox"
            />
          </v-list>
        </v-menu>
      </v-btn>
      <v-spacer />
      <div v-if="emails.results" class="d-flex align-center">
        <div class="text-caption mr-2">
          {{ emails.first_index }}-{{ emails.last_index }} {{ $gettext('on') }}
          {{ emails.count }}
        </div>
        <div>
          <v-btn
            icon="mdi-chevron-left"
            size="x-small"
            :disabled="emails.prev_page === null"
            @click="page = emails.prev_page"
          />
          <v-btn
            icon="mdi-chevron-right"
            size="x-small"
            :disabled="emails.next_page === null"
            @click="page = emails.next_page"
          />
        </div>
      </div>
    </v-toolbar>
  </v-card>
  <v-skeleton-loader v-if="loading" type="card@2"></v-skeleton-loader>
  <template v-else>
    <div class="emails position-absolute top-0 bottom-0 w-100 overflow-y-auto">
      <template v-if="emails.results?.length">
        <v-card
          v-for="email in emails.results"
          :key="email.imapid"
          density="compact"
          class="mb-2 mx-1"
        >
          <v-card-text
            class="d-flex align-center"
            :class="{ 'font-weight-bold': email.style === 'unseen' }"
          >
            <v-checkbox
              v-model="selection"
              :value="email.imapid"
              hide-details
            />
            <v-btn
              :icon="email.flagged ? 'mdi-star' : 'mdi-star-outline'"
              variant="flat"
              @click="toggleFollowState(email)"
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
      <v-alert
        v-else
        class="mt-4"
        type="info"
        :text="$gettext('No message yet in this mailbox')"
        variant="tonal"
      />
    </div>
  </template>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import api from '@/api/webmail'

const props = defineProps({
  mailbox: {
    type: String,
    default: 'INBOX',
  },
})

const { $gettext } = useGettext()
const { displayNotification, reloadMailboxCounters } = useBusStore()
const router = useRouter()
const route = useRoute()

const loading = ref(false)
const emails = ref({})
const page = ref(1)
const search = ref('')
const selectAll = ref(false)
const selection = ref([])
const working = ref(false)

let intervalId = null

const currentMailbox = computed(() => {
  return route.query.mailbox || 'INBOX'
})

const openEmail = (emailid) => {
  router.push({
    name: 'EmailView',
    query: { mailbox: props.mailbox, mailid: emailid },
  })
}

const fetchEmails = () => {
  emails.value = {}
  loading.value = true
  api
    .getMailboxEmails(props.mailbox, { page: page.value, search: search.value })
    .then((resp) => {
      emails.value = resp.data
      loading.value = false
    })
    .catch(() => {
      loading.value = false
    })
}

const autoRefreshContent = () => {
  fetchEmails()
}

const submitSearch = () => {
  if (search.value) {
    fetchEmails()
  }
}

const toggleAllSelection = (value) => {
  if (!value) {
    selection.value = []
  } else {
    selection.value = emails.value.results.map((email) => email.imapid)
  }
}

const deleteSelection = () => {
  if (!selection.value.length) {
    return
  }
  working.value = true
  api.deleteSelection(currentMailbox.value, selection.value).then(() => {
    working.value = false
    displayNotification({ msg: $gettext('Message(s) deleted') })
    fetchEmails()
    reloadMailboxCounters()
  })
}

const markSelectionAsJunk = () => {
  if (!selection.value.length) {
    return
  }
  working.value = true
  api.markSelectionAsJunk(currentMailbox.value, selection.value).then(() => {
    working.value = false
    displayNotification({ msg: $gettext('Message(s) marked as junk') })
    autoRefreshContent()
  })
}

const markSelectionAsNotJunk = () => {
  if (!selection.value.length) {
    return
  }
  working.value = true
  api.markSelectionAsNotJunk(currentMailbox.value, selection.value).then(() => {
    working.value = false
    displayNotification({ msg: $gettext('Message(s) marked as not junk') })
    autoRefreshContent()
  })
}

const flagSelection = (status) => {
  if (!selection.value.length) {
    return
  }
  working.value = true
  api.flagSelection(currentMailbox.value, selection.value, status).then(() => {
    working.value = false
    selection.value = []
    displayNotification({ msg: $gettext('Message(s) flagged') })
    fetchEmails()
    reloadMailboxCounters()
  })
}

const emptyMailbox = () => {
  loading.value = true
  api.emptyUserMailbox(currentMailbox.value).then(() => {
    emails.value = {}
    loading.value = false
    reloadMailboxCounters()
  })
}

const toggleFollowState = async (email) => {
  const flag = email.flagged ? 'unflagged' : 'flagged'
  await api.flagSelection(currentMailbox.value, [email.imapid], flag)
  email.flagged = flag === 'flagged'
}

onMounted(() => {
  intervalId = setInterval(autoRefreshContent, 300 * 1000)
})

onUnmounted(() => {
  clearInterval(intervalId)
})

watch(
  () => props.mailbox,
  () => {
    fetchEmails()
  },
  { immediate: true }
)
watch(selection, () => {
  if (!selection.value.length) {
    selectAll.value = false
  } else {
    selectAll.value = true
  }
})
watch(page, () => {
  fetchEmails()
})
</script>

<style lang="scss" scoped>
.v-card-text {
  padding: 0;
}
.emails {
  margin-top: 150px;
}
.clickable {
  cursor: pointer;
}
</style>
