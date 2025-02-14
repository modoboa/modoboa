<template>
  <CreationForm
    ref="form"
    :title="$gettext('New domain')"
    :steps="steps"
    :form-getter="getForm"
    :get-v-form-ref="getVFormRef"
    :validate-object="validateDomain"
    :summary-sections="summarySections"
    @close="close"
    @create="submit"
  >
    <template #[`form.general`]>
      <DomainGeneralForm ref="general" v-model="domain" class="ml-4" />
    </template>

    <template #[`form.dns`]>
      <DomainDNSForm ref="dns" v-model="domain" class="ml-4" />
    </template>
    <template #[`form.limitations`]>
      <DomainLimitationsForm ref="limitations" v-model="domain" class="ml-4" />
    </template>
    <template #[`form.options`]>
      <DomainOptionsForm
        ref="options"
        v-model="domain"
        class="ml-4"
        @create-admin="updateCreateAdmin"
      />
    </template>
    <template #[`form.transport`]>
      <DomainTransportForm
        ref="transport"
        v-model="domain.transport"
        class="ml-4"
      />
    </template>
    <template #[`item.random_password`]="{ item }">
      <template v-if="item.value">
        <v-col cols="12" class="highligth text-white">
          <v-row>
            <v-col
              ><span>{{ item.key }}</span></v-col
            >
            <v-col class="text-right">{{ $yesno(item.value) }}</v-col>
          </v-row>
          <v-row>
            <v-col class="text-right py-1">
              {{ domain.domain_admin.password }}
              <v-btn
                icon="mdi-clipboard-multiple-outline"
                color="white"
                variant="text"
                :title="$gettext('Copy to clipboard')"
                @click="copyPassword"
              ></v-btn>
            </v-col>
          </v-row>
        </v-col>
      </template>
      <template v-else>
        <v-col
          ><span class="text-grey">{{ item.key }}</span></v-col
        >
        <v-col class="text-right">{{ $yesno(item.value) }}</v-col>
      </template>
    </template>
  </CreationForm>
</template>

<script setup lang="js">
import ParametersApi from '@/api/parameters.js'
import CreationForm from '@/components/tools/CreationForm.vue'
import DomainGeneralForm from './form_steps/DomainGeneralForm.vue'
import DomainDNSForm from './form_steps/DomainDNSForm.vue'
import DomainLimitationsForm from './form_steps/DomainLimitationsForm.vue'
import DomainOptionsForm from './form_steps/DomainOptionsForm.vue'
import DomainTransportForm from './form_steps/DomainTransportForm.vue'
import { useGettext } from 'vue3-gettext'
import { ref, computed, onMounted } from 'vue'
import { useBusStore, useDomainsStore } from '@/stores'
import { useRouter } from 'vue-router'

const { $gettext } = useGettext()
const busStore = useBusStore()
const domainsStore = useDomainsStore()
const router = useRouter()

const emit = defineEmits(['close'])

const defaultDomain = {
  name: '',
  type: 'domain',
  enabled: true,
  enable_dns_checks: true,
  enable_dkim: false,
  dkim_key_selector: 'modoboa',
  quota: 0,
  default_mailbox_quota: 0,
  domain_admin: {
    username: 'admin',
    random_password: false,
    with_mailbox: false,
    with_aliases: false,
  },
  transport: { settings: {} },
}

const domain = ref(defaultDomain)

onMounted(() => {
  //TODO : Store this in Pinia
  ParametersApi.getGlobalApplication('admin').then((resp) => {
    const params = resp.data.params
    domain.value.quota = params.default_domain_quota
    domain.value.default_mailbox_quota = params.default_mailbox_quota
    if (params.default_domain_message_limit !== null) {
      domain.value.message_limit = params.default_domain_message_limit
    }
  })
})

const createAdmin = ref(false)

// Reference to steps components
const general = ref()
const dns = ref()
const limitations = ref()
const options = ref()
const transport = ref()

// Object to reference
const formStepsComponents = {
  general: general,
  dns: dns,
  limitations: limitations,
  options: options,
  transport: transport,
}

const domainSteps = [
  { name: 'general', title: $gettext('General') },
  { name: 'dns', title: $gettext('DNS') },
  { name: 'limitations', title: $gettext('Limitations') },
  { name: 'options', title: $gettext('Options') },
]
const relaySteps = [
  { name: 'general', title: $gettext('General') },
  { name: 'dns', title: $gettext('DNS') },
  { name: 'limitations', title: $gettext('Limitations') },
  { name: 'transport', title: $gettext('Transport') },
]

const steps = computed(() => {
  return domain.value.type === 'domain' ? domainSteps : relaySteps
})

const summarySections = computed(() => {
  const result = [
    {
      title: $gettext('General'),
      items: [
        { key: $gettext('Name'), value: domain.value.name },
        { key: $gettext('Type'), value: domain.value.type },
        {
          key: $gettext('Enabled'),
          value: domain.value.enabled,
          type: 'yesno',
        },
      ],
    },
    {
      title: $gettext('DNS'),
      items: [
        {
          key: $gettext('Enable DNS checks'),
          value: domain.value.enable_dns_checks,
          type: 'yesno',
        },
        {
          key: $gettext('Enable DKIM signing'),
          value: domain.value.enable_dkim,
          type: 'yesno',
        },
      ],
    },
    {
      title: $gettext('Limitations'),
      items: [
        { key: $gettext('Quota'), value: domain.value.quota },
        {
          key: $gettext('Default mailbox quota'),
          value: domain.value.default_mailbox_quota,
        },
        {
          key: $gettext('Message sending limit'),
          value: domain.value.message_limit,
        },
      ],
    },
  ]
  if (domain.value.enable_dkim) {
    result[1].items.push({
      key: $gettext('DKIM key selector'),
      value: domain.value.dkim_key_selector,
    })
    result[1].items.push({
      key: $gettext('DKIM key length'),
      value: domain.value.dkim_key_length,
    })
  }
  if (domain.value.type === 'relaydomain' && domain.value.transport.service) {
    const relayEntry = {
      title: $gettext('Transport'),
      items: [
        {
          key: $gettext('Service'),
          value: domain.value.transport.service,
        },
      ],
    }
    for (const setting of transport.value.service.settings) {
      const item = {
        key: setting.label,
        value:
          domain.value.transport.settings[
            `${domain.value.transport.service}_${setting.name}`
          ],
      }
      if (setting.type === 'boolean') {
        item.type = 'yesno'
      }
      relayEntry.items.push(item)
    }
    result.push(relayEntry)
  } else if (domain.value.type === 'domain') {
    const options = {
      title: $gettext('Options'),
      items: [
        {
          key: $gettext('Create a domain administrator'),
          value: createAdmin.value,
          type: 'yesno',
        },
      ],
    }
    if (createAdmin.value) {
      options.items.push(
        {
          key: $gettext('Administrator name'),
          value: domain.value.domain_admin.username,
        },
        {
          name: 'random_password',
          key: $gettext('Random password'),
          value: domain.value.domain_admin.random_password,
          type: 'yesno',
        },
        {
          key: $gettext('With mailbox'),
          value: domain.value.domain_admin.with_mailbox,
          type: 'yesno',
        },
        {
          key: $gettext('Create aliases'),
          value: domain.value.domain_admin.with_aliases,
          type: 'yesno',
        }
      )
    }
    result.push(options)
  }
  return result
})

function close() {
  emit('close')
}

function copyPassword() {
  navigator.clipboard.writeText(domain.value.domain_admin.password).then(() => {
    busStore.displayNotification({
      msg: $gettext('Password copied to clipboard'),
    })
  })
}

function getForm(step) {
  return formStepsComponents.value[step.name]
}
function getVFormRef(step) {
  return formStepsComponents[step.name].value.vFormRef
}

async function validateDomain() {}

function updateCreateAdmin(value) {
  createAdmin.value = value
}

function submit() {
  const data = JSON.parse(JSON.stringify(domain.value))
  if (!createAdmin.value) {
    delete data.domain_admin
  }
  if (data.message_limit === '') {
    delete data.message_limit
  }
  if (data.type === 'relaydomain') {
    transport.value.checkSettingTypes(data)
  } else {
    delete data.transport
  }
  domainsStore.createDomain(data).then((resp) => {
    router.push({ name: 'DomainDetail', params: { id: resp.data.pk } })
    busStore.displayNotification({ msg: $gettext('Domain created') })
    close()
  })
}
</script>

<style lang="scss">
.highligth {
  background-color: #515d78;
}
</style>
