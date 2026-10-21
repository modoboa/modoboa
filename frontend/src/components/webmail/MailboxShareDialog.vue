<template>
  <v-card>
    <v-card-title>
      <span class="headline">{{ $gettext('Share this mailbox') }}</span>
    </v-card-title>
    <v-card-text>
      <p class="mb-4 text-medium-emphasis">
        {{ $gettext('Its subfolders are shared too.') }}
      </p>
      <v-form ref="formRef" @submit.prevent="submit">
        <div class="d-flex">
          <v-select
            v-model="currentShare.grantee"
            :label="$gettext('Account')"
            :error-messages="formErrors.grantee"
            :items="candidates"
            item-title="name"
            item-value="address"
            variant="outlined"
            density="compact"
          >
            <template #item="{ props: itemProps, item }">
              <v-list-item v-bind="itemProps" :subtitle="item.address" />
            </template>
          </v-select>
          <v-select
            v-model="currentShare.level"
            :label="$gettext('Access')"
            :error-messages="formErrors.level"
            :items="levels"
            variant="outlined"
            density="compact"
            class="ml-4"
          />
          <v-btn
            color="primary"
            icon="mdi-content-save-outline"
            type="submit"
            size="small"
            class="ml-4"
            :title="$gettext('Save')"
            :loading="working"
            :disabled="!currentShare.grantee || !currentShare.level"
          />
        </div>
      </v-form>
      <v-table>
        <thead>
          <tr>
            <th>{{ $gettext('Account') }}</th>
            <th>{{ $gettext('Access') }}</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!shares.length">
            <td colspan="3" class="text-medium-emphasis">
              {{ $gettext('This mailbox is not shared') }}
            </td>
          </tr>
          <tr v-for="share in shares" :key="share.grantee">
            <td>{{ getGranteeName(share.grantee) }}</td>
            <td>{{ getLevelLabel(share.level) }}</td>
            <td class="text-right">
              <v-btn
                v-if="isCandidate(share.grantee)"
                icon="mdi-pencil"
                size="x-small"
                variant="flat"
                :title="$gettext('Edit')"
                @click="editShare(share)"
              />
              <v-btn
                icon="mdi-trash-can"
                size="x-small"
                variant="flat"
                :title="$gettext('Stop sharing')"
                :disabled="working"
                @click="deleteShare(share)"
              />
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn @click="emit('close')">{{ $gettext('Close') }}</v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import api from '@/api/webmail'

const props = defineProps({
  mailbox: {
    type: String,
    required: true,
  },
})
const emit = defineEmits(['close'])

const { $gettext } = useGettext()

const levels = computed(() => [
  { title: $gettext('Read'), value: 'read' },
  { title: $gettext('Read and write'), value: 'write' },
  { title: $gettext('Read, write and manage subfolders'), value: 'manage' },
])

const candidates = ref([])
const shares = ref([])
const currentShare = ref({ level: 'read' })
const formErrors = ref({})
const working = ref(false)

function getGranteeName(grantee) {
  const candidate = candidates.value.find((c) => c.address === grantee)
  return candidate ? candidate.name : grantee
}

function isCandidate(grantee) {
  return candidates.value.some((c) => c.address === grantee)
}

function getLevelLabel(level) {
  const item = levels.value.find((l) => l.value === level)
  // Rights set by another mail client
  return item ? item.title : $gettext('Custom')
}

async function fetchShares() {
  const resp = await api.getMailboxShares(props.mailbox)
  shares.value = resp.data.shares
}

function editShare(share) {
  currentShare.value = {
    grantee: share.grantee,
    level: share.level === 'custom' ? 'read' : share.level,
  }
}

// Errors are notified by the API client
/**
 * Run a change of the shares, then display them again.
 *
 * @return {Error|null} the error of the request, already notified by the
 *   API client
 */
async function run(request) {
  working.value = true
  try {
    await request()
    return null
  } catch (err) {
    return err
  } finally {
    // Even after a failure: the subfolders may have been partly updated
    await fetchShares().catch(() => {})
    working.value = false
  }
}

async function submit() {
  const err = await run(() =>
    api.shareMailbox({ mailbox: props.mailbox, ...currentShare.value })
  )
  formErrors.value = err?.response?.data || {}
  if (!err) {
    currentShare.value = { level: 'read' }
  }
}

async function deleteShare(share) {
  await run(() =>
    api.unshareMailbox({ mailbox: props.mailbox, grantee: share.grantee })
  )
}

api.getShareCandidates().then((resp) => {
  candidates.value = resp.data
})
fetchShares()
</script>
