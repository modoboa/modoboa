<template>
  <LoadingData v-if="!aliasesStore.aliasesLoaded || working" />
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
                    {{ $gettext('Address') }}:
                    {{ editedAlias.address }}
                  </v-col>
                  <v-col cols="6">
                    <div class="mr-2">
                      {{ $gettext('Enabled') }}
                    </div>
                    <v-icon v-if="editedAlias.enabled" color="success"
                      >mdi-check-circle-outline</v-icon
                    >
                    <v-icon v-else>mdi-close-circle-outline</v-icon>
                  </v-col>
                </v-row>
              </v-fade-transition>
            </v-col>
          </v-row>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <AliasGeneralForm ref="generalForm" v-model="editedAlias" />
        </v-expansion-panel-text>
      </v-expansion-panel>
      <v-expansion-panel eager value="recipientForm">
        <v-expansion-panel-title v-slot="{ expanded }">
          <v-row no-gutters>
            <v-col cols="4">
              {{ $gettext('Recipients') }}
            </v-col>
            <v-col cols="8" class="text-medium-emphasis">
              <v-fade-transition leave-absolute>
                <span v-if="expanded"></span>
                <v-row v-else no-gutters style="width: 100%">
                  <v-chip
                    v-for="(rcpt, index) in editedAlias.recipients"
                    :key="index"
                    size="small"
                  >
                    {{ rcpt }}
                  </v-chip>
                </v-row>
              </v-fade-transition>
            </v-col>
          </v-row>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <AliasRecipientForm
            ref="recipientForm"
            v-model="editedAlias.recipients"
          />
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
    <div class="mt-4 d-flex justify-end">
      <v-btn :loading="working" @click="$router.go(-1)">
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
import { useIdentitiesStore, useAliasesStore } from '@/stores'
import AliasGeneralForm from './form_steps/AliasGeneralForm.vue'
import AliasRecipientForm from './form_steps/AliasRecipientForm'
import LoadingData from '@/components/tools/LoadingData.vue'
import { useGettext } from 'vue3-gettext'
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const { $gettext } = useGettext()
const identitiesStore = useIdentitiesStore()
const aliasesStore = useAliasesStore()
const route = useRoute()
const router = useRouter()

const editedAlias = ref({ pk: route.params.id })

const panel = ref(0)
const working = ref(false)
const formErrors = ref(false)

// refs
const generalForm = ref()
const recipientForm = ref()

//formMap
const formMap = { generalForm: generalForm, recipientForm: recipientForm }

async function save() {
  formErrors.value = false
  panel.value = []
  for (const [panelName, formRef] of Object.entries(formMap)) {
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

  identitiesStore
    .updateIdentity('alias', editedAlias.value)
    .then(() =>
      router.push({
        name: 'AliasDetail',
        params: { id: route.params.id },
      })
    )
    .finally(() => (working.value = false))
}

onMounted(() => {
  aliasesStore.getAlias(route.params.id).then((response) => {
    editedAlias.value = { ...response.data }
  })
})
</script>
