<template>
  <v-card>
    <v-form ref="vFormRef" @submit.prevent="submit">
      <v-card-title>
        <span class="headline">{{ title }}</span>
      </v-card-title>
      <v-card-text>
        <label class="m-label">{{ $gettext('Name') }}</label>
        <v-text-field
          v-model="form.name"
          variant="outlined"
          density="compact"
          :rules="[rules.required]"
        />
        <label class="m-label">{{ $gettext('Choose a domain') }}</label>
        <v-select
          v-model="form.target"
          :items="domains"
          item-title="name"
          item-value="pk"
          :rules="[rules.required]"
          single-line
          variant="outlined"
          density="compact"
        />
        <v-switch v-model="form.enabled" label="Enabled" color="primary" />
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn :loading="working" @click="emit('close')">
          {{ $gettext('Close') }}
        </v-btn>
        <v-btn
          v-if="domainAlias && domainAlias.pk"
          color="error"
          :loading="working"
          @click="deleteAlias"
        >
          {{ $gettext('Delete') }}
        </v-btn>
        <v-btn color="primary" type="submit" :loading="working">
          {{ submitLabel }}
        </v-btn>
      </v-card-actions>
    </v-form>
  </v-card>
</template>

<script setup lang="js">
import { useGettext } from 'vue3-gettext'
import { computed, ref, onMounted } from 'vue'
import { useBusStore } from '@/stores'
import rules from '@/plugins/rules.js'
import domainsApi from '@/api/domains'

const { $gettext } = useGettext()

const emit = defineEmits(['close'])
const { displayNotification } = useBusStore()

const props = defineProps({
  domainAlias: { type: Object, default: () => null },
})

const domains = ref([])
const form = ref({ enabled: true })
const working = ref(false)
const vFormRef = ref()

const submitLabel = computed(() => {
  return props.domainAlias ? $gettext('Update') : $gettext('Add')
})

const title = computed(() =>
  props.domainAlias
    ? $gettext('Edit domain alias')
    : $gettext('Add a new domain alias')
)

async function deleteAlias() {
  working.value = true
  try {
    await domainsApi.deleteDomainAlias(props.domainAlias.pk)
    displayNotification({ msg: $gettext('Domain alias deleted') })
    emit('close')
  } finally {
    working.value = false
  }
}

async function submit() {
  const { valid } = await vFormRef.value.validate()
  if (!valid) {
    return
  }
  working.value = true
  try {
    if (!form.value.pk) {
      await domainsApi.createDomainAlias(form.value)
      displayNotification({ msg: $gettext('Domain alias created') })
    } else {
      const data = JSON.parse(JSON.stringify(form.value))
      await domainsApi.updateDomainAlias(props.domainAlias.pk, data)
      displayNotification({ msg: $gettext('Domain alias updated') })
    }
    emit('close')
  } finally {
    working.value = false
  }
}

onMounted(() => {
  domainsApi.getDomains().then((resp) => {
    domains.value = resp.data
  })
  if (props.domainAlias) {
    form.value = JSON.parse(JSON.stringify(props.domainAlias))
  }
})
</script>
