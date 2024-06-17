<template>
  <div>
    <v-card flat>
      <v-card-title>
        <span class="text-subtitle-1">
          {{ $gettext('WebAuthn') }}
        </span>
      </v-card-title>
      <v-card-text>
        <template v-if="fidoCreds.length === 0">
          <div tag="p" class="my-4">
            {{
              $gettext(
                "You don't have any WebAuthN registered as a second authentication method."
              )
            }}
          </div>
        </template>
        <template v-else>
          <h3>{{ $gettext('Registered Webauthn devices') }}</h3>
          <v-data-table-virtual
            :headers="headers"
            :items="fidoCreds"
            height="400"
            item-value="id"
          >
            <template #[`item.added_on`]="{ item }">
              {{ $date(item.added_on) }}
            </template>
            <template #[`item.last_used`]="{ item }">
              <template v-if="item.last_used === null">
                {{ $gettext('Never') }}
              </template>
              <template v-else>
                {{ $date(item.last_used) }}
              </template>
            </template>
            <template #[`item.actions`]="{ item }">
              <v-icon class="me-2" size="small" @click="editCred(item)">
                mdi-pencil
              </v-icon>
              <v-icon size="small" @click="deleteCred(item)">
                mdi-delete
              </v-icon>
            </template>
          </v-data-table-virtual>
        </template>
        <template v-if="browserCapable">
          <v-form ref="fidoForm" @submit.prevent="startFidoRegistration">
            <v-text-field
              v-model="name"
              :label="$gettext('Name')"
              :rules="[rules.required]"
            />
            <v-btn color="success" type="submit" :loading="registrationLoading">
              {{ $gettext('Add WebAuthN device') }}
            </v-btn>
          </v-form>
        </template>
        <template v-else>
          <v-alert type="error">
            {{
              $gettext('Your browser does not seem compatible with WebAuthN')
            }}
          </v-alert>
        </template>
      </v-card-text>
    </v-card>
  </div>
  <ConfirmDialog ref="confirmDeletion" />
  <ConfirmDialog ref="confirmEdition" :callback_agree="checkForm">
    <v-form ref="editForm">
      <v-text-field
        v-model="editName"
        :label="$gettext('name')"
        :rules="[rules.required]"
      />
      <v-switch
        v-model="editEnabled"
        :label="$gettext('enabled')"
        color="principal"
      />
    </v-form>
  </ConfirmDialog>
</template>

<script setup lang="js">
import { ref, onMounted, computed } from 'vue'
import authApi from '@/api/auth.js'
import { useGettext } from 'vue3-gettext'
import rules from '@/plugins/rules.js'
import { useAuthStore } from '@/stores'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import {
  create,
  parseCreationOptionsFromJSON,
} from '@github/webauthn-json/browser-ponyfill'

const authStore = useAuthStore()

const { $gettext } = useGettext()

const name = ref()
const registrationLoading = ref(false)
const browserCapable = !!(
  navigator.credentials &&
  navigator.credentials.create &&
  navigator.credentials.get &&
  window.PublicKeyCredential
)
const fidoForm = ref()
const fidoCreds = computed(() => authStore.fidoCreds)
const headers = [
  { title: '#', key: 'id' },
  { title: $gettext('Name'), key: 'name' },
  { title: $gettext('Added On'), key: 'added_on' },
  { title: $gettext('Last Used'), key: 'last_used' },
  { title: $gettext('Use count'), key: 'use_count' },
  { title: $gettext('Enabled'), key: 'enabled' },
  { title: $gettext('Actions'), key: 'actions' },
]
const confirmDeletion = ref()
const confirmEdition = ref()
const editForm = ref()
const editName = ref('')
const editEnabled = ref(false)

async function startFidoRegistration() {
  registrationLoading.value = true
  const { valid } = await fidoForm.value.validate()
  if (!valid) {
    registrationLoading.value = false
    return
  }
  const creationOption = await authApi.beginFidoRegistration()
  console.log(creationOption)
  if (creationOption) {
    const options = parseCreationOptionsFromJSON(creationOption.data)
    const result = await create(options)
    const response = result.toJSON()
    response.name = name.value
    console.log(response)
    authStore.addFidoCred(response)
  }
}

async function deleteCred(cred) {
  const result = await confirmDeletion.value.open(
    $gettext('Warning'),
    $gettext('Do you really want to delete this WebaAuthn device?'),
    {
      color: 'warning',
      cancelLabel: $gettext('No'),
      agreeLabel: $gettext('Yes'),
    }
  )
  if (!result) {
    return
  }
  authStore.deleteFidoCreds(cred.id)
}

async function checkForm() {
  return (await editForm.value.validate()).valid
}

async function editCred(cred) {
  editName.value = cred.name
  editEnabled.value = cred.enabled

  const result = await confirmEdition.value.open(
    $gettext('Edtion'),
    $gettext('Edit your device'),
    {
      color: 'warning',
      cancelLabel: $gettext('Cancel'),
      agreeLabel: $gettext('Save'),
    }
  )
  if (!result) {
    return
  }

  data = { name: editName.value, enabled: editEnabled.value }
  //TODO : send it !
}

onMounted(() => {
  authStore.getFidoCreds()
})
</script>
