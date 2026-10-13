<template>
  <v-combobox
    v-model:search="search"
    :model-value="model"
    :items="items"
    :item-title="displayRecipient"
    :placeholder="$gettext('Provide one or more addresses')"
    :rules="[...rules, validRecipients]"
    variant="outlined"
    density="compact"
    hide-details="auto"
    chips
    closable-chips
    multiple
    @update:model-value="update"
    @update:search="lookForRecipients"
  >
    <template #chip="{ props: chipProps, item }">
      <v-chip
        v-bind="chipProps"
        :color="isValidRecipient(item) ? undefined : 'error'"
      />
    </template>
  </v-combobox>
</template>

<script setup>
import { ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import debounce from 'debounce'
import {
  displayRecipient,
  formatRecipient,
  isValidRecipient,
  splitRecipients,
  uniqueRecipients,
  useRecentRecipients,
} from '@/composables/webmail'
import contactsApi from '@/api/contacts'

defineProps({
  rules: {
    type: Array,
    default: () => [],
  },
})

// Recipients as given to the API: "Name" <address>, or address
const model = defineModel({ type: Array, default: () => [] })

const { $ngettext } = useGettext()
const recentRecipients = useRecentRecipients()

// Suggestions: recent recipients first, then the addresses of contacts
const items = ref([])
const search = ref('')
let lastSearch = ''

// Pasted lists are split, an address is given once
const update = (values) => {
  model.value = uniqueRecipients(values.flatMap(splitRecipients))
}

const validRecipients = (values) => {
  const invalid = (values || []).filter((value) => !isValidRecipient(value))
  if (!invalid.length) {
    return true
  }
  return $ngettext(
    'Invalid address: %{addresses}',
    'Invalid addresses: %{addresses}',
    invalid.length,
    { addresses: invalid.map(displayRecipient).join(', ') }
  )
}

const lookForRecipients = debounce(async (value) => {
  lastSearch = value
  if (!value) {
    items.value = []
    return
  }
  const recent = recentRecipients.search(value)
  let addresses
  try {
    addresses = (await contactsApi.getEmailAddresses({ search: value })).data
  } catch {
    // Already displayed to the user by the API client
    return
  }
  // The answer to a previous search must not replace the current one
  if (value !== lastSearch) {
    return
  }
  const contacts = addresses.map((item) =>
    formatRecipient({ name: item.display_name.trim(), address: item.address })
  )
  items.value = uniqueRecipients([...recent, ...contacts])
}, 300)
</script>
