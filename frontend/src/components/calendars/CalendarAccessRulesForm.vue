<template>
  <v-card>
    <v-card-title>
      <span class="headline">{{ $gettext('Calendar sharing') }}</span>
    </v-card-title>
    <v-card-text>
      <v-form ref="formRef" @submit.prevent="submit">
        <div class="d-flex">
          <v-select
            v-model="currentRule.mailbox"
            :label="$gettext('Full address')"
            :form-errors="formErrors['mailbox']"
            :items="mailboxes"
            item-title="full_address"
            return-object
            variant="outlined"
            density="compact"
          />
          <v-checkbox
            v-model="currentRule.read"
            :label="$gettext('Read')"
            class="ml-4"
          />
          <v-checkbox
            v-model="currentRule.write"
            :label="$gettext('Write')"
            class="ml-4"
          />
          <v-spacer />
          <v-btn
            color="primary"
            icon="mdi-content-save-outline"
            type="submit"
            size="small"
          />
        </div>
      </v-form>
      <br />
      <v-table>
        <thead>
          <tr>
            <th>{{ $gettext('Account') }}</th>
            <th>{{ $gettext('Read') }}</th>
            <th>{{ $gettext('Write') }}</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="rule in accessRules" :key="rule.pk">
            <td>{{ rule.mailbox.full_address }}</td>
            <td>
              <v-icon :icon="rule.read ? 'mdi-check' : 'mdi-close'" />
            </td>
            <td>
              <v-icon :icon="rule.write ? 'mdi-check' : 'mdi-close'" />
            </td>
            <td>
              <v-btn
                icon="mdi-pencil"
                size="x-small"
                variant="flat"
                @click="editRule(rule)"
              />
              <v-btn
                icon="mdi-trash-can"
                size="x-small"
                variant="flat"
                @click="deleteRule(rule)"
              />
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn @click="close">{{ $gettext('Close') }}</v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/api/calendars'
import mailboxesApi from '@/api/mailboxes'

const props = defineProps({
  calendarPk: {
    type: Number,
    default: 0,
  },
})
const emit = defineEmits(['close'])

const accessRules = ref([])
const mailboxes = ref([])
const currentRule = ref({})
const formErrors = ref({})

api.getAccessRules(props.calendarPk).then((response) => {
  accessRules.value = response.data
  if (!accessRules.value.length) {
    accessRules.value = []
  }
})
mailboxesApi.getAll().then((response) => {
  mailboxes.value = response.data
})

async function submit() {
  if (!currentRule.value.pk) {
    currentRule.value.calendar = props.calendarPk
    api.createAccessRule(currentRule.value).then((response) => {
      accessRules.value.push(response.data)
      resetForm()
    }, onError)
  } else {
    api.updateAccessRule(currentRule.value.pk, currentRule.value).then(() => {
      accessRules.value.filter((item, pos) => {
        if (item.pk === currentRule.value.pk) {
          accessRules.value[pos] = currentRule.value
        }
      })
      resetForm()
    }, onError)
  }
}

function resetForm() {
  currentRule.value = {}
  formErrors.value = {}
}
function onError(response) {
  formErrors.value = response.data
}
function editRule(rule) {
  currentRule.value = JSON.parse(JSON.stringify(rule))
}
function deleteRule(rule) {
  api.deleteAccessRule(rule.pk).then(() => {
    accessRules.value = accessRules.value.filter((localRule) => {
      return localRule.pk !== rule.pk
    })
  })
}
function close() {
  formErrors.value = {}
  emit('close')
}
</script>
