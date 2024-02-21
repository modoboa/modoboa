<template>
  <v-form ref="vFormRef">
    <v-text-field
      v-model="provider.name"
      :label="$gettext('Provider name')"
      variant="outlined"
      :rules="[rules.required]"
    />
    <v-text-field
      v-model="provider.address"
      :label="$gettext('Address (hostname or IP)')"
      :rules="[rules.required]"
      variant="outlined"
    />
    <v-text-field
      v-model="provider.port"
      :label="$gettext('IMAP Port')"
      type="number"
      variant="outlined"
      :rules="[rules.required, rules.portNumber]"
    />
    <v-switch
      v-model="provider.secured"
      :label="$gettext('Secured')"
      color="primary"
      :hint="
        $gettext('Is the IMAP connection secured using SSL/TLS or StartTLS')
      "
      persistent-hint
    />
    <div class="my-7">
      <v-btn :loading="loading" color="primary" @click="checkConnection">
        {{ $gettext('Check connection:') }}
        <v-icon v-if="connectionStatus === 0" color="blue-grey-darken-2">
          mdi-help-circle-outline
        </v-icon>
        <v-icon v-else-if="connectionStatus === 1" color="success">
          mdi-check-all
        </v-icon>
        <v-icon v-else color="warning"> mdi-alert-circle-outline </v-icon>
        <template #loader>
          <span class="custom-loader">
            <v-icon light>mdi-cached</v-icon>
          </span>
        </template>
      </v-btn>
    </div>
  </v-form>
</template>

<script setup lang="js">
import ProviderApi from '@/api/imap_migration/providers'
import rules from '@/plugins/rules'
import { computed, ref } from 'vue'

const props = defineProps({ modelValue: { type: Object, default: null } })

const provider = computed(() => props.modelValue)

const connectionStatus = ref(0)
const loading = ref(false)

const vFormRef = ref()

async function checkConnection() {
  const valid = await vFormRef.value.validate()
  if (!valid) {
    return
  }
  loading.value = true
  const params = {
    address: provider.value.address,
    port: provider.value.port,
    secured: provider.value.secured,
  }
  ProviderApi.checkProvider(params)
    .then(() => {
      connectionStatus.value = 1
    })
    .catch((error) => {
      console.log(error)
      connectionStatus.value = 2
    })
    .finally(() => (loading.value = false))
}

defineExpose({ vFormRef })
</script>

<style>
.custom-loader {
  animation: loader 1s infinite;
  display: flex;
}
@-moz-keyframes loader {
  from {
    transform: rotate(0);
  }
  to {
    transform: rotate(360deg);
  }
}
@-webkit-keyframes loader {
  from {
    transform: rotate(0);
  }
  to {
    transform: rotate(360deg);
  }
}
@-o-keyframes loader {
  from {
    transform: rotate(0);
  }
  to {
    transform: rotate(360deg);
  }
}
@keyframes loader {
  from {
    transform: rotate(0);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
