<template>
  <CreationForm
    ref="form"
    :title="$gettext('New account')"
    :steps="steps"
    :form-getter="getForm"
    :get-v-form-ref="getVFormRef"
    :validate-object="validateAccount"
    :summary-sections="summarySections"
    @close="close"
    @create="submit"
    @validation-error="setFormErrors"
  >
    <template #[`form.role`]>
      <AccountRoleForm ref="role" v-model="account" />
    </template>
    <template #[`form.identification`]>
      <AccountGeneralForm ref="identification" v-model="account" />
    </template>
    <template #[`form.mailbox`]>
      <AccountMailboxForm ref="mailbox" v-model="account" />
    </template>
    <template #[`form.aliases`]>
      <AccountAliasForm ref="aliases" v-model="account" />
    </template>
    <template #[`item.random_password`]="{ item }">
      <template v-if="item.value">
        <v-col cols="12" class="highligth text-white">
          <v-row>
            <v-col
              ><span>{{ item.key }}</span></v-col
            >
            <v-col v-if="item.type === 'yesno'" class="text-right">
              {{ $yesno(item.value) }}
            </v-col>
          </v-row>
          <v-row>
            <v-col class="text-right py-1">
              <v-btn
                append-icon="mdi-clipboard-multiple-outline"
                color="white"
                variant="text"
                :title="$gettext('Copy to clipboard')"
                @click="copyPassword"
              >
                {{ account.password }}
              </v-btn>
            </v-col>
          </v-row>
        </v-col>
      </template>
      <template v-else>
        <v-col
          ><span class="grey--text">{{ item.key }}</span></v-col
        >
        <v-col v-if="item.type === 'yesno'" class="text-right">{{
          $yesno(item.value)
        }}</v-col>
      </template>
    </template>
  </CreationForm>
</template>

<script setup lang="js">
import accountsApi from '@/api/accounts'
import CreationForm from '@/components/tools/CreationForm.vue'
import AccountRoleForm from './form_steps/AccountRoleForm.vue'
import AccountGeneralForm from './form_steps/AccountGeneralForm.vue'
import AccountMailboxForm from './form_steps/AccountMailboxForm.vue'
import AccountAliasForm from './form_steps/AccountAliasForm.vue'

import { useGettext } from 'vue3-gettext'
import { ref, computed, onMounted } from 'vue'
import { useBusStore, useDomainsStore, useIdentitiesStore } from '@/stores'

const { $gettext } = useGettext()
const busStore = useBusStore()
const domainsStore = useDomainsStore()
const identitiesStore = useIdentitiesStore()
const emit = defineEmits(['close', 'created'])

const needsMailbox = computed(
  () =>
    account.value.role !== 'SuperAdmins' &&
    account.value.username &&
    account.value.username.indexOf('@') !== -1
)

const summarySections = computed(() => {
  const result = [
    {
      title: $gettext('Role'),
      items: [{ key: $gettext('Role'), value: account.value.role }],
    },
    {
      title: $gettext('Identification'),
      items: [
        { key: $gettext('Username'), value: account.value.username },
        {
          key: $gettext('First name'),
          value: account.value.first_name,
        },
        { key: $gettext('Last name'), value: account.value.last_name },
        {
          name: 'random_password',
          key: $gettext('Random password'),
          value: account.value.random_password,
          type: 'yesno',
        },
        {
          key: $gettext('Enabled'),
          value: account.value.is_active,
          type: 'yesno',
        },
      ],
    },
  ]
  if (needsMailbox.value) {
    return result.concat([
      {
        title: $gettext('Mailbox'),
        items: [
          {
            key: $gettext('Email'),
            value: account.value.mailbox.full_address,
          },
          {
            key: $gettext('Quota'),
            value: account.value.mailbox.use_domain_quota
              ? $gettext('Domain default value')
              : account.value.mailbox.quota,
          },
          {
            key: $gettext('Message sending limit'),
            value: account.value.mailbox.message_limit,
          },
          {
            key: $gettext('Send only account'),
            value: account.value.mailbox.is_send_only,
            type: 'yesno',
          },
        ],
      },
      {
        title: $gettext('Aliases'),
        items: [
          {
            key: $gettext('Aliases'),
            value: account.value.aliases,
            type: 'list',
          },
        ],
      },
    ])
  }
  return result
})

const steps = computed(() => {
  const result = [
    {
      name: 'role',
      title: $gettext('Role'),
    },
    {
      name: 'identification',
      title: $gettext('Identification'),
    },
  ]
  if (needsMailbox.value) {
    return result.concat([
      {
        name: 'mailbox',
        title: $gettext('Mailbox'),
      },
      {
        name: 'aliases',
        title: $gettext('Aliases'),
      },
    ])
  }
  return result
})

const account = ref({
  aliases: [],
  is_active: true,
  role: 'SimpleUsers',
  mailbox: {
    use_domain_quota: true,
  },
  random_password: false,
})

// Form refs
const role = ref()
const identification = ref()
const mailbox = ref()
const aliases = ref()

const formStepsComponents = {
  role: role,
  identification: identification,
  mailbox: mailbox,
  aliases: aliases,
}

function copyPassword() {
  navigator.clipboard.writeText(account.value.password).then(() => {
    busStore.displayNotification({
      msg: $gettext('Password copied to clipboard'),
    })
  })
}

function getForm(step) {
  return formStepsComponents.step[step.name]
}

function getVFormRef(step) {
  return formStepsComponents[step.name].value.vFormRef
}

function setFormErrors(step, errors) {
  const stepName = steps.value[step - 1].name
  if (formStepsComponents[stepName].value.formErrors) {
    formStepsComponents[stepName].value.formErrors.value = errors
  }
}

function preparePayload(payload) {
  const cleaned_payload = { ...payload }
  if (
    cleaned_payload.role === 'SuperAdmins' &&
    cleaned_payload.username &&
    cleaned_payload.username.indexOf('@') === -1
  ) {
    delete cleaned_payload.mailbox
  }
  if (cleaned_payload.mailbox && cleaned_payload.mailbox.message_limit === '') {
    cleaned_payload.mailbox.message_limit = null
  }
  return cleaned_payload
}

function validateAccount() {
  const payload = preparePayload({ ...account.value })
  return accountsApi.validate(payload)
}

function close() {
  emit('close')
}

function submit() {
  const data = preparePayload({ ...account.value })
  identitiesStore.createIdentity('account', data).then(() => {
    emit('created')
    close()
  })
}

onMounted(() => {
  domainsStore.getDomains()
})
</script>

<style lang="scss">
.highligth {
  background-color: #515d78;
}
</style>
