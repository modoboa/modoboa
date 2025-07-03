<template>
  <ConnectedLayout>
    <template #navbar>
      <v-navigation-drawer
        v-model="drawer"
        :rail="rail"
        permanent
        color="primary"
        app
      >
        <template #prepend>
          <div class="d-flex align-center">
            <v-img
              src="@/assets/Modoboa_RVB-BLANC-SANS.png"
              max-width="190"
              class="logo"
            />
            <v-btn
              :icon="rail ? 'mdi-chevron-right' : 'mdi-chevron-left'"
              variant="text"
              @click.stop="rail = !rail"
            >
            </v-btn>
          </div>

          <div class="d-flex justify-center mb-4">
            <v-btn
              :text="$gettext('Compose')"
              color="secondary"
              variant="flat"
              prepend-icon="mdi-pencil"
              @click="openComposeForm"
            />
          </div>
        </template>
        <MailboxList
          v-model="selectedMailbox"
          :mailboxes="userMailboxes"
          class="mr-2"
          @update:model-value="openMailbox"
        />
        <template #append>
          <div class="border-t-sm d-flex align-center bg-grey">
            <v-btn class="ml-2" variant="text" icon size="small">
              <v-icon icon="mdi-cog" />
              <v-menu activator="parent">
                <v-list density="compact">
                  <v-list-item
                    :title="$gettext('Create a new mailbox')"
                    prepend-icon="mdi-plus"
                    @click="openMailboxForm"
                  />
                  <v-list-item
                    :title="$gettext('Edit this mailbox')"
                    prepend-icon="mdi-pencil"
                    :disabled="readOnlyMailbox"
                    @click="editMailbox"
                  />
                  <v-list-item
                    :title="$gettext('Delete this mailbox')"
                    prepend-icon="mdi-trash-can"
                    :disabled="readOnlyMailbox"
                    @click="deleteMailbox"
                  />
                  <v-list-item
                    :title="$gettext('Compress this mailbox')"
                    prepend-icon="mdi-folder-zip-outline"
                    @click="compressMailbox"
                  />
                </v-list>
              </v-menu>
            </v-btn>

            <v-progress-linear
              v-if="mailboxQuota"
              :color="quotaColor"
              :model-value="mailboxQuota.usage"
              :title="mailboxQuotaTitle"
            />
          </div>
        </template>
      </v-navigation-drawer>
    </template>
  </ConnectedLayout>
  <v-dialog v-model="showMailboxForm" max-width="800">
    <MailboxForm
      :user-mailboxes="userMailboxes"
      :mailbox="editedMailbox"
      :hdelimiter="hdelimiter"
      @mailbox-renamed="navigateToMailbox"
      @close="closeMailboxForm()"
    />
  </v-dialog>
  <ConfirmDialog ref="confirm" />
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import ConnectedLayout from '@/layouts/connected/ConnectedLayout.vue'
import MailboxForm from '@/components/webmail/MailboxForm.vue'
import MailboxList from '@/components/webmail/MailboxList.vue'
import api from '@/api/webmail'

const { $gettext } = useGettext()
const route = useRoute()
const router = useRouter()
const busStore = useBusStore()

const confirm = ref()
const drawer = ref(true)
const rail = ref(false)
const editedMailbox = ref(null)
const hdelimiter = ref(null)
const mailboxQuota = ref(null)
const selectedMailbox = ref(route.query.mailbox || 'INBOX')
const showMailboxForm = ref(false)
const userMailboxes = ref([])

const readOnlyMailbox = computed(() => {
  const mailboxes = ['INBOX']
  return mailboxes.includes(route.query.mailbox || 'INBOX')
})

const quotaColor = computed(() => {
  if (mailboxQuota.value.usage < 50) {
    return 'info'
  }
  if (mailboxQuota.value.usage < 80) {
    return 'warning'
  }
  return 'error'
})

const mailboxQuotaTitle = computed(() => {
  return `${mailboxQuota.value.current} / ${mailboxQuota.value.limit} (${mailboxQuota.value.usage}%)`
})

function openMailbox(mailbox) {
  router.push({
    name: 'MailboxView',
    query: { mailbox },
  })
  api.getUserMailboxQuota(mailbox).then((resp) => {
    mailboxQuota.value = resp.data
  })
}

const fetchUserMailboxes = async () => {
  const resp = await api.getUserMailboxes()
  userMailboxes.value = resp.data.mailboxes
  hdelimiter.value = resp.data.hdelimiter
}

const openComposeForm = () => {
  router.push({ name: 'ComposeEmailView' })
}

const closeMailboxForm = () => {
  showMailboxForm.value = false
  editedMailbox.value = null
  fetchUserMailboxes()
}

const openMailboxForm = () => {
  showMailboxForm.value = true
}

const editMailbox = () => {
  editedMailbox.value = selectedMailbox.value
  showMailboxForm.value = true
}

const navigateToMailbox = (mailbox) => {
  selectedMailbox.value = mailbox
  router.push({
    name: 'MailboxView',
    query: { mailbox },
  })
}

const compressMailbox = async () => {
  await api.compressUserMailbox({ name: selectedMailbox.value })
  busStore.displayNotification({ msg: $gettext('Mailbox compressed') })
}

const deleteMailbox = async () => {
  const confirmed = await confirm.value.open(
    $gettext('Warning'),
    $gettext('Delete this mailbox?'),
    {
      color: 'warning',
      agreeLabel: $gettext('Yes'),
      cancelLabel: $gettext('No'),
    }
  )
  if (!confirmed) {
    return
  }
  await api.deleteUserMailbox({ name: selectedMailbox.value })
  busStore.displayNotification({ msg: $gettext('Mailbox deleted') })
  navigateToMailbox('INBOX')
}

watch(
  () => busStore.dataKey,
  () => {
    fetchUserMailboxes()
  }
)

await fetchUserMailboxes()
const resp = await api.getUserMailboxQuota(route.query.mailbox || 'INBOX')
mailboxQuota.value = resp.data
</script>
