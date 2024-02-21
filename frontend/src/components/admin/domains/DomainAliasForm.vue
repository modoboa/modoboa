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
          dense
          variant="outlined"
          :rules="[rules.required]"
        />
        <label class="m-label">{{ $gettext('Choose a domain') }}</label>
        <v-select
          v-model="form.target"
          :items="Object.values(domainsStore.domains)"
          item-title="name"
          item-value="pk"
          :rules="[rules.required]"
          single-line
          dense
          variant="outlined"
        />
        <v-switch v-model="form.enabled" label="Enabled" color="primary" />
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn @click="emit('close')">
          {{ $gettext('Close') }}
        </v-btn>
        <v-btn
          v-if="domainAlias && domainAlias.pk"
          color="error"
          @click="deleteAlias"
        >
          {{ $gettext('Delete') }}
        </v-btn>
        <v-btn color="primary" type="submit">
          {{ submitLabel }}
        </v-btn>
      </v-card-actions>
    </v-form>
  </v-card>
</template>

<script setup lang="js">
import { useGettext } from 'vue3-gettext'
import { useDomainsStore } from '@/stores'
import { computed, ref, onMounted } from 'vue'
import rules from '@/plugins/rules.js'

const { $gettext } = useGettext()
const domainsStore = useDomainsStore()

const emit = defineEmits(['close'])

const props = defineProps({
  domainAlias: { type: Object, default: () => null },
})

const form = ref({ enabled: true })

const vFormRef = ref()

const submitLabel = computed(() => {
  return props.domainAlias ? $gettext('Update') : $gettext('Add')
})

const title = computed(() =>
  props.domainAlias
    ? $gettext('Edit domain alias')
    : $gettext('Add a new domain alias')
)

function deleteAlias() {
  domainsStore.deleteAlias(props.domainAlias).then(() => emit('close'))
}

async function submit() {
  const { valid } = await vFormRef.value.validate()
  if (!valid) {
    return
  }
  try {
    if (!form.value.pk) {
      // Create
      domainsStore.createAlias(form.value).then(() => {
        emit('close')
      })
    } else {
      // Update
      const data = JSON.parse(JSON.stringify(form.value))
      domainsStore.updateAlias(data).then(() => emit('close'))
    }
  } catch (error) {
    //TODO
    console.error(error)
  }
}

onMounted(() => {
  if (props.domainAlias) {
    form.value = JSON.parse(JSON.stringify(props.domainAlias))
  }
})
</script>
