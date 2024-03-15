<template>
  <v-card v-if="!token" flat>
    <v-card-text>
      {{ $gettext('Your API token has not been generated yet.') }}
    </v-card-text>
    <v-card-actions>
      <v-btn
        color="success"
        variant="flat"
        :loading="loading"
        @click="generateKey"
      >
        {{ $gettext('Generate') }}
      </v-btn>
    </v-card-actions>
  </v-card>
  <v-card v-else flat>
    <v-card-text>
      <label class="m-label">
        {{ $gettext('Your API token is:') }}
      </label>
      <code class="ml-5 mr-5">
        {{ token }}
      </code>
      <v-btn
        icon="mdi-clipboard-plus"
        density="compact"
        :title="$gettext('Copy token to clipboard')"
        variant="text"
        @click="copyToClipboard()"
      >
      </v-btn>
      <v-btn
        icon="mdi-delete"
        density="compact"
        color="error"
        variant="text"
        :title="$gettext('Delete token')"
        @click="openDeletionDialog"
      >
      </v-btn>
    </v-card-text>
  </v-card>
  <v-alert type="info" variant="tonal" border="start" class="mt-4">
    {{ $gettext('A documentation of the API is available') }}
    <a :href="apiDocUrl" target="_blank">{{ $gettext('here') }}</a
                                                               >.
  </v-alert>
  <ConfirmDialog ref="confirm" @agree="deleteToken" />
</template>

<script setup>
import accountApi from '@/api/account'
import { useBusStore } from '@/stores'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import { ref, computed, inject, onMounted } from 'vue'
import { useGettext } from 'vue3-gettext'

const { $gettext } = useGettext()
const busStore = useBusStore()

const $config = inject('$config')

const apiDocUrl = computed(() => $config.API_DOC_URL)

const loading = ref(false)
const token = ref(null)
const confirm = ref()

function copyToClipboard() {
  navigator.clipboard.writeText(token.value)
  busStore.displayNotification({
    msg: $gettext('API token copied to your clipboard'),
    type: 'success',
  })
}

function generateKey() {
  loading.value = true
  accountApi
    .createAPIToken()
    .then((resp) => {
      token.value = resp.data.token
      busStore.displayNotification({
        msg: $gettext('API token created'),
        type: 'success',
      })
    })
    .finally(() => (loading.value = false))
}

function openDeletionDialog() {
  confirm.value.open(
    $gettext('Warning'),
    $gettext('You are about to delete your API access token'),
    {
      color: 'error',
      cancelLabel: $gettext('Cancel'),
      agreeLabel: $gettext('Proceed'),
    }
  )
}

async function deleteToken() {
  await accountApi.deleteAPIToken()
  busStore.displayNotification({
    msg: $gettext('API token deleted'),
    type: 'success',
  })
  token.value = null
}

onMounted(() => {
  accountApi.getAPIToken().then((resp) => {
    token.value = resp.data.token
  })
})
</script>
