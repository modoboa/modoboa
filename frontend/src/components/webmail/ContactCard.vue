<template>
  <v-card min-width="300">
    <v-list>
      <v-list-item
        :subtitle="model.name ? model.address : ''"
        :title="model.name || model.address"
      >
        <template #append>
          <v-btn
            v-if="!model.contact_id"
            color="secondary"
            icon="mdi-card-account-mail-outline"
            variant="text"
            :loading="working"
            :title="$gettext('Add to contacts')"
            @click="addContact"
          ></v-btn>
          <v-btn
            v-else
            icon="mdi-pencil"
            variant="text"
            :loading="working"
            :title="$gettext('Update contact')"
            @click="redirectToContacts"
          ></v-btn>
        </template>
      </v-list-item>
    </v-list>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import contactsApi from '@/api/contacts'

const model = defineModel()

const router = useRouter()
const { $gettext } = useGettext()
const { displayNotification } = useBusStore()

const working = ref(false)

const addContact = async () => {
  const body = {
    emails: [{ address: model.value.address, type: 'other' }],
  }
  if (model.value.name) {
    body.display_name = model.value.name
  } else {
    body.display_name = model.value.address
  }
  working.value = true
  let resp
  try {
    resp = await contactsApi.createContact(body)
    model.value.contact_id = resp.data.pk
  } finally {
    working.value = false
  }
  displayNotification({ msg: $gettext('Contact added to address book') })
}

const redirectToContacts = () => {
  router.push({ name: 'ContactList' })
}
</script>
