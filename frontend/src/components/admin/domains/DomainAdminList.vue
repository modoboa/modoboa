<template>
  <v-card>
    <v-card-title>
      <span class="headline">
        <div v-if="dialogMode" class="headline">
          {{ $gettext('Administrators of') }} {{ domain.name }}
        </div>
        <div v-else class="headline">
          {{ $gettext('Administrators') }}
        </div>
      </span>
    </v-card-title>
    <v-card-text>
      <v-data-table-virtual :headers="adminHeaders" :items="administrators">
        <template #[`item.username`]="{ item }">
          <span v-if="item.id">{{ item.username }}</span>
          <v-autocomplete
            v-else
            v-model="selectedAccount"
            :label="$gettext('Select an account')"
            :items="accounts"
            item-title="username"
            class="mt-5"
            return-object
          >
            <template #append>
              <v-btn
                v-if="selectedAccount"
                variant="text"
                color="primary"
                size="x-large"
                @click="addAdministrator"
              >
                <v-icon>mdi-content-save</v-icon>
              </v-btn>
            </template>
          </v-autocomplete>
        </template>
        <template #[`item.name`]="{ item }">
          {{ item.first_name }} {{ item.last_name }}
        </template>
        <template #[`item.actions`]="{ item }">
          <v-btn
            v-if="item.id"
            variant="text"
            color="red"
            :title="$gettext('Remove this administrator')"
            size="x-large"
            @click="removeAdministrator(item)"
          >
            <v-icon>mdi-delete-outline</v-icon>
          </v-btn>
        </template>
      </v-data-table-virtual>
    </v-card-text>
    <v-card-actions>
      <v-row>
        <v-col :align="dialogMode ? 'left' : 'right'">
          <v-btn
            v-if="!hideAddBtn"
            color="primary"
            variant="outlined"
            @click="addRow"
          >
            <v-icon small>mdi-plus</v-icon>
            {{ $gettext('Add administrator') }}
          </v-btn>
        </v-col>
        <v-col v-if="dialogMode" align="right">
          <v-btn color="grey darken-1" variant="text" @click="close">
            {{ $gettext('Close') }}
          </v-btn>
        </v-col>
      </v-row>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import accountApi from '@/api/accounts'
import domainApi from '@/api/domains'
import { useBusStore } from '@/stores'
import { useGettext } from 'vue3-gettext'
import { ref, onMounted } from 'vue'

const busStore = useBusStore()
const { $gettext } = useGettext()

const props = defineProps({
  domain: {
    type: Object,
    default: () => {},
  },
  dialogMode: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close'])

const accounts = ref([])
const administrators = ref([])

const adminHeaders = ref([
  { title: $gettext('Username'), value: 'username' },
  { title: $gettext('Name'), value: 'name' },
  { title: '', value: 'actions', align: 'end', sortable: false },
])

const hideAddBtn = ref(false)
const selectedAccount = ref(null)

function addRow() {
  administrators.value.push({})
  hideAddBtn.value = true
}

function close() {
  hideAddBtn.value = false
  emit('close')
}
function fetchAdministrators(domain) {
  domainApi.getDomainAdministrators(domain.pk).then((resp) => {
    administrators.value = resp.data
  })
}

function fetchAccounts() {
  accountApi.getAll({ role: 'DomainAdmins' }).then((resp) => {
    accounts.value = resp.data.filter(
      (account) =>
        administrators.value.find((admin) => admin.id === account.pk) ===
        undefined
    )
  })
}
function addAdministrator() {
  domainApi
    .addDomainAdministrator(props.domain.pk, selectedAccount.value.pk)
    .then(() => {
      fetchAdministrators(props.domain)
      accounts.value = accounts.value.filter(
        (account) => account.pk !== selectedAccount.value.pk
      )
      selectedAccount.value = null
      hideAddBtn.value = false
      busStore.displayNotification({
        msg: $gettext('Administrator added'),
      })
    })
}

function removeAdministrator(admin) {
  domainApi.removeDomainAdministrator(props.domain.pk, admin.id).then(() => {
    fetchAdministrators(props.domain)
    fetchAccounts()
    busStore.displayNotification({ msg: $gettext('Administrator removed') })
  })
}

onMounted(() => {
  fetchAdministrators(props.domain)
  fetchAccounts()
})
</script>
