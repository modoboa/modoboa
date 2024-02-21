<template>
  <v-expansion-panels v-model="panel">
    <v-expansion-panel>
      <v-expansion-panel-title v-slot="{ open }">
        <v-row no-gutters>
          <v-col cols="4">
            {{ $gettext('General') }}
          </v-col>
          <v-col cols="8" class="text-secondary">
            <v-fade-transition leave-absolute>
              <span v-if="open"></span>
              <v-row v-else no-gutters style="width: 100%">
                <v-col cols="6">
                  {{ $gettext('Name:') }}
                  {{ editedProvider.name }}
                </v-col>
              </v-row>
            </v-fade-transition>
          </v-col>
        </v-row>
      </v-expansion-panel-title>
      <v-expansion-panel-text>
        <ProviderGeneralForm ref="generalForm" v-model="editedProvider" />
      </v-expansion-panel-text>
    </v-expansion-panel>
    <v-expansion-panel>
      <v-expansion-panel-title v-slot="{ open }">
        <v-row no-gutters>
          <v-col cols="4">
            {{ $gettext('Associated domains') }}
          </v-col>
          <v-col cols="8" class="text-secondary">
            <v-fade-transition leave-absolute>
              <span v-if="open"></span>
              <v-row v-else no-gutters style="width: 100%">
                <v-col v-if="editedProvider.domains.length > 0" cols="6">
                  {{ $gettext('Number of associated domains:') }}
                  {{ editedProvider.domains.length }}
                </v-col>
                <v-col v-else cols="6">
                  {{ $gettext('No associated domains') }}
                </v-col>
              </v-row>
            </v-fade-transition>
          </v-col>
        </v-row>
      </v-expansion-panel-title>
      <v-expansion-panel-text>
        <ProviderAssociatedForm
          ref="associatedForm"
          v-model="editedProvider.domains"
        />
      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
  <div class="mt-4 d-flex justify-end">
    <v-btn @click="$router.go(-1)">
      {{ $gettext('Cancel') }}
    </v-btn>
    <v-btn class="ml-4" color="primary darken-1" @click="save">
      {{ $gettext('Save') }}
    </v-btn>
  </div>
</template>

<script setup lang="js">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useBusStore, useProvidersStore } from '@/stores'
import { useGettext } from 'vue3-gettext'
import providers from '@/api/imap_migration/providers'
import ProviderGeneralForm from './form_steps/ProviderGeneralForm.vue'
import ProviderAssociatedForm from './form_steps/ProviderAssociatedForm.vue'

const props = defineProps({
  provider: {
    type: Object,
    default: null,
  },
})

const { $gettext } = useGettext()
const busStore = useBusStore()
const router = useRouter()
const providersStore = useProvidersStore()

const editedProvider = ref({
  domains: [],
})
const panel = ref(0)
const generalForm = ref()
const associatedForm = ref()

watch(
  () => props.provider,
  (val) => {
    if (val) {
      editedProvider.value = { ...val }
      if (!editedProvider.value.domains) {
        editedProvider.value.domains = []
      }
    }
  },
  { immediate: true }
)

async function save() {
  if (generalForm.value !== undefined) {
    const { valid } = await generalForm.value.vFormRef.validate()
    if (!valid) {
      return
    }
  }
  if (associatedForm.value !== undefined) {
    const { valid } = await associatedForm.value.vFormRef.validate()
    if (!valid) {
      return
    }
  }
  try {
    const data = { ...editedProvider.value }
    data.domains = []
    for (const domain of editedProvider.value.domains) {
      if (domain.new_domain) {
        data.domains.push({
          name: domain.name,
          new_domain: domain.new_domain.pk || domain.new_domain.id,
        })
      } else {
        data.domains.push(domain)
      }
    }
    await providers.patchProvider(editedProvider.value.id, data).then(() => {
      busStore.displayNotification({
        msg: $gettext('Provider updated'),
      })
      providersStore.getProviders()
      router.push({ name: 'ProvidersList' })
    })
  } catch (error) {
    if (generalForm.value) {
      generalForm.value.$refs.observer.setErrors(error.response.data)
    }
    if (associatedForm.value) {
      associatedForm.value.$refs.observer.setErrors(error.response.data)
    }
  }
}
</script>
