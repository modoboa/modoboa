<template>
  <v-form ref="vFormRef">
    <v-switch
      v-if="!alias.pk"
      v-model="alias.random"
      :label="$gettext('Random address')"
      color="primary"
    />
    <template v-if="!alias.random">
      <label class="m-label">{{ $gettext('Email address') }}</label>
      <EmailField
        ref="address"
        v-model="alias.address"
        type="email"
        variant="outlined"
        density="compact"
        :rules="[rules.required]"
      />
    </template>
    <template v-else>
      <label class="m-label">{{ $gettext('Domain') }}</label>
      <v-select
        v-model="alias.domain"
        :items="Object.values(domains)"
        item-title="name"
        return-object
        variant="outlined"
        density="compact"
        :rules="[rules.required]"
        @update:model-value="updateAddress"
      >
        <template #append>
          <v-btn variant="flat" icon="mdi-reload" @click="updateAddress" />
        </template>
      </v-select>
      <v-text-field
        v-model="alias.address"
        :label="$gettext('Generated address')"
        readonly
      >
        <template #append-inner>
          <v-btn
            variant="flat"
            icon="mdi-clipboard-outline"
            @click="copyAlias"
          />
        </template>
      </v-text-field>
    </template>
    <v-switch
      v-model="alias.enabled"
      :label="$gettext('Enabled')"
      color="primary"
    />
    <label class="m-label">{{ $gettext('Expire at') }}</label>
    <v-text-field v-model="alias.expire" variant="outlined" density="compact" />
    <label class="m-label">{{ $gettext('Description') }}</label>
    <v-textarea
      v-model="alias.description"
      rows="2"
      variant="outlined"
      density="compact"
    />
  </v-form>
</template>

<script setup lang="js">
import aliasesApi from '@/api/aliases'
import EmailField from '@/components/tools/EmailField'
import { ref, computed } from 'vue'
import { useDomainsStore } from '@/stores'
import rules from '@/plugins/rules'

const domainsStore = useDomainsStore()
const props = defineProps({ modelValue: { type: Object, default: null } })

const alias = computed(() => props.modelValue)

const domains = computed(() => domainsStore.domains)

const vFormRef = ref()

function copyAlias() {
  if (alias.value.address != null) {
    navigator.clipboard.writeText(alias.value.address)
  }
}

async function updateAddress() {
  if (alias.value.domain != null)
    aliasesApi.getRandomAddress().then((resp) => {
      alias.value.address = `${resp.data.address}@${alias.value.domain.name}`
    })
}

defineExpose({ vFormRef })
</script>
