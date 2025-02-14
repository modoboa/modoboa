<template>
  <LoadingData v-if="!domainsStore.domainsLoaded || working" />
  <div v-else>
    <v-expansion-panels v-model="panel" :multiple="formErrors">
      <v-expansion-panel eager value="generalForm">
        <v-expansion-panel-title v-slot="{ expanded }">
          <v-row no-gutters>
            <v-col cols="4">
              {{ $gettext('General') }}
            </v-col>
            <v-col cols="8" class="text-medium-emphasis">
              <v-fade-transition leave-absolute>
                <span v-if="expanded"></span>
                <v-row v-else no-gutters style="width: 100%">
                  <v-col cols="6">
                    {{ $gettext('Name: ') }}
                    {{ editedDomain.name }}
                  </v-col>
                  <v-col cols="6">
                    {{ $gettext('Type: ') }}
                    {{ editedDomain.type }}
                  </v-col>
                </v-row>
              </v-fade-transition>
            </v-col>
          </v-row>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <DomainGeneralForm ref="generalForm" v-model="editedDomain" />
        </v-expansion-panel-text>
      </v-expansion-panel>
      <v-expansion-panel eager value="dnsForm">
        <v-expansion-panel-title v-slot="{ expanded }">
          <v-row no-gutters>
            <v-col cols="4">
              {{ $gettext('DNS') }}
            </v-col>
            <v-col cols="8" class="text-medium-emphasis">
              <v-fade-transition leave-absolute>
                <span v-if="expanded"></span>
                <v-row v-else no-gutters style="width: 100%">
                  <v-col cols="6">
                    {{ $gettext('DNS checks') }}
                    <v-icon
                      v-if="editedDomain.enable_dns_checks"
                      color="success"
                      icon="mdi-check-circle-outline"
                    />
                    <v-icon v-else icon="mdi-check-circle-outline" />
                  </v-col>
                  <v-col cols="6">
                    {{ $gettext('DKIM signing') }}
                    <v-icon
                      v-if="editedDomain.enable_dkim"
                      color="success"
                      icon="mdi-check-circle-outline"
                    />
                    <v-icon v-else icon="mdi-close-circle-outline" />
                  </v-col>
                </v-row>
              </v-fade-transition>
            </v-col>
          </v-row>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <DomainDNSForm ref="dnsForm" v-model="editedDomain" />
        </v-expansion-panel-text>
      </v-expansion-panel>
      <v-expansion-panel eager value="limitationForm">
        <v-expansion-panel-title v-slot="{ expanded }">
          <v-row no-gutters>
            <v-col cols="4">
              {{ $gettext('Limitations') }}
            </v-col>
            <v-col cols="8" class="text-medium-emphasis">
              <v-fade-transition leave-absolute>
                <span v-if="expanded"></span>
                <v-row v-else no-gutters style="width: 100%">
                  <v-col cols="6">
                    <div class="mr-2">
                      {{ $gettext('Quota: ') }}
                      {{ editedDomain.quota }}
                    </div>
                  </v-col>
                  <v-col v-if="editedDomain.message_limit" cols="6">
                    <div class="mr-2">
                      {{ $gettext('Sending limit: ') }}
                      {{ editedDomain.message_limit }}
                    </div>
                  </v-col>
                  <v-col v-else cols="6">
                    <div class="mr-2">
                      {{ $gettext('No sending limit') }}
                    </div>
                  </v-col>
                </v-row>
              </v-fade-transition>
            </v-col>
          </v-row>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <DomainLimitationsForm ref="limitationForm" v-model="editedDomain" />
        </v-expansion-panel-text>
      </v-expansion-panel>
      <v-expansion-panel
        v-if="editedDomain.type === 'relaydomain'"
        value="transportForm"
        eager
      >
        <v-expansion-panel-title v-slot="{ expanded }">
          <v-row no-gutters>
            <v-col cols="4">
              {{ $gettext('Transport') }}
            </v-col>
            <v-col cols="8" class="text-medium-emphasis">
              <v-fade-transition leave-absolute>
                <span v-if="expanded"></span>
                <v-row v-else no-gutters style="width: 100%">
                  <v-col cols="6">
                    <div class="mr-2">
                      {{ $gettext('Service: ') }}
                      {{ editedDomain.transport.service }}
                    </div>
                  </v-col>
                </v-row>
              </v-fade-transition>
            </v-col>
          </v-row>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <DomainTransportForm
            ref="transportForm"
            v-model="editedDomain.transport"
          />
        </v-expansion-panel-text>
      </v-expansion-panel>
      <v-expansion-panel
        v-if="
          limitsConfig.params &&
          limitsConfig.params.enable_domain_limits &&
          (authUser.role === 'SuperAdmins' || authUser.role === 'Resellers')
        "
        value="resourcesForm"
        eager
      >
        <v-expansion-panel-title>
          <v-row no-gutters>
            <v-col cols="4">
              {{ $gettext('Resources') }}
            </v-col>
          </v-row>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <ResourcesForm ref="resourcesForm" v-model="editedDomain.resources" />
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
    <div class="mt-4 d-flex justify-end">
      <v-btn :loading="working" @click="router.go(-1)">
        {{ $gettext('Cancel') }}
      </v-btn>
      <v-btn
        class="ml-4"
        color="primary darken-1"
        :loading="working"
        @click="save"
      >
        {{ $gettext('Save') }}
      </v-btn>
    </div>
  </div>
</template>

<script setup lang="js">
import DomainDNSForm from './form_steps/DomainDNSForm.vue'
import DomainGeneralForm from './form_steps/DomainGeneralForm.vue'
import DomainLimitationsForm from './form_steps/DomainLimitationsForm.vue'
import DomainTransportForm from './form_steps/DomainTransportForm.vue'
import LoadingData from '@/components/tools/LoadingData.vue'
import parametersApi from '@/api/parameters'
import ResourcesForm from '@/components/tools/ResourcesForm.vue'
import { computed, ref, onMounted } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useAuthStore, useDomainsStore } from '@/stores'
import { useRouter } from 'vue-router'

const router = useRouter()
const { $gettext } = useGettext()
const authStore = useAuthStore()
const domainsStore = useDomainsStore()

const props = defineProps({ domain: { type: Object, default: null } })

const authUser = computed(() => authStore.authUser)

const limitsConfig = ref({})
const panel = ref(0)
const working = ref(false)

const editedDomain = computed(() => props.domain)

//refs
const generalForm = ref()
const resourcesForm = ref()
const transportForm = ref()
const limitationForm = ref()
const dnsForm = ref()

// Form map
const formMap = computed(() => {
  const map = {
    generalForm: generalForm,
    limitationForm: limitationForm,
    dnsForm: dnsForm,
  }
  if (editedDomain.value.type === 'relaydomain') {
    map.transportForm = transportForm
  }
  if (
    limitsConfig.value.params &&
    limitsConfig.value.params.enable_domain_limits &&
    (authUser.value.role === 'SuperAdmins' ||
      authUser.value.role === 'Resellers')
  ) {
    map.resourcesForm = resourcesForm
  }
  return map
})

const formErrors = ref(false)

async function save() {
  formErrors.value = false
  panel.value = []
  for (const [panelName, formRef] of Object.entries(formMap.value)) {
    if (formRef.value != null) {
      const { valid } = await formRef.value.vFormRef.validate()
      if (!valid) {
        formErrors.value = true
        panel.value.push(panelName)
      }
    }
  }
  if (formErrors.value) {
    return
  }
  working.value = true
  try {
    const data = JSON.parse(JSON.stringify(editedDomain.value))
    if (data.transport === null) {
      delete data.transport
    }
    if (data.type === 'relaydomain') {
      transportForm.value.checkSettingTypes(data)
    }
    domainsStore.updateDomain(data).then(() => {
      router.go(-1)
    })
  } finally {
    working.value = false
  }
}
onMounted(() => {
  parametersApi.getGlobalApplication('limits').then((resp) => {
    limitsConfig.value.data = resp.data
  })
})
</script>
