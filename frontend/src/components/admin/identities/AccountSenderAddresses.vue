<template>
  <v-card>
    <v-card-title>
      <span class="headline">{{ $gettext('Sender addresses') }}</span>
    </v-card-title>
    <v-card-text>
      <v-data-table
        :headers="headers"
        :items="addresses"
        :no-data-text="$gettext('No sender address defined for this account')"
      >
        <template #[`item.address`]="{ item }">
          <span v-if="item.pk">{{ item.address }}</span>
          <v-text-field
            v-else
            v-model="newAddress"
            :label="$gettext('Specify an email address')"
          >
            <template #append>
              <v-btn
                v-if="newAddress"
                icon="mdi-content-save"
                color="primary"
                variant="text"
                @click="submit"
              >
              </v-btn>
            </template>
          </v-text-field>
        </template>
        <template #[`item.actions`]="{ item }">
          <v-btn
            v-if="item.pk"
            icon="mdi-delete-outline"
            color="red"
            :title="$gettext('Remove this address')"
            variant="text"
            @click="deleteSenderAddress(item)"
          >
          </v-btn>
        </template>
        <template #bottom></template>
      </v-data-table>
      <v-btn
        v-if="!hideAddBtn"
        size="small"
        color="primary"
        variant="outlined"
        @click="addRow"
      >
        <v-icon size="small" icon="mdi-plus"></v-icon>
        {{ $gettext('Add sender address') }}
      </v-btn>
    </v-card-text>
  </v-card>
</template>

<script setup lang="js">
import { ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import senderAddresses from '@/api/senderAddresses'

const busStore = useBusStore()
const { $gettext } = useGettext()
const props = defineProps({ account: { type: Object, default: null } })

const addresses = ref([])
const hideAddBtn = ref(false)
const newAddress = ref('')

const headers = [
  { title: $gettext('Address'), key: 'address' },
  { title: '', key: 'actions', align: 'end', sortable: false },
]

function addRow() {
  addresses.value.push({})
  hideAddBtn.value = true
}

function fetchSenderAddresses() {
  senderAddresses.getAllForMailbox(props.account.mailbox.pk).then((resp) => {
    addresses.value = resp.data
  })
}

function submit() {
  const data = {
    address: newAddress.value,
    mailbox: props.account.mailbox.pk,
  }
  senderAddresses.create(data).then(() => {
    fetchSenderAddresses()
    newAddress.value = null
    hideAddBtn.value = false
    busStore.displayNotification({ msg: $gettext('Sender address added') })
  })
}

function deleteSenderAddress(senderAddress) {
  senderAddresses.delete(senderAddress.pk).then(() => {
    fetchSenderAddresses()
    busStore.displayNotification({ msg: $gettext('Sender address deleted') })
  })
}

fetchSenderAddresses()
</script>
