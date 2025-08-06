<template>
  <v-card v-if="props.domain">
    <v-card-title>
      <div class="headline">{{ $gettext('Transport') }}</div>
    </v-card-title>
    <v-card-text>
      <v-row>
        <v-col cols="6">{{ $gettext('Service') }}</v-col>
        <v-col cols="6">{{ props.domain.transport.service }}</v-col>
      </v-row>
      <template v-if="currentBackend">
        <v-row v-for="(setting, index) in currentBackend.settings" :key="index">
          <v-col cols="6">{{ setting.label }}</v-col>
          <v-col cols="6">
            <template v-if="setting.type !== 'boolean'">
              {{ getSettingValue(setting.name) }}
            </template>
            <template v-else>
              <BooleanIcon
                :value="getSettingValue(setting.name)"
                variant="flat"
              />
            </template>
          </v-col>
        </v-row>
      </template>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { computed, ref } from 'vue'
import transportApi from '@/api/transports'
import BooleanIcon from '@/components/tools/BooleanIcon'

const props = defineProps({
  domain: {
    type: Object,
    default: null,
  },
})

const backends = ref([])

const currentBackend = computed(() => {
  return backends.value.find(
    (backend) => backend.name === props.domain.transport.service
  )
})

const getSettingValue = (name) => {
  return props.domain.transport.settings[`${currentBackend.value.name}_${name}`]
}

const resp = await transportApi.getAll()
backends.value = resp.data
</script>
