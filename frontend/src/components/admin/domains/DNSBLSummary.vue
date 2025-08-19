<template>
  <v-card>
    <v-card-title class="text-h5">
      <span>
        {{ $gettext('DNSBL summary for ') }} {{ props.mxrecord.name }}
      </span>
    </v-card-title>
    <v-card-text>
      {{
        $gettext(
          'IP address %{ address } is currently listed by the following DNSBL providers:',
          { address: mxrecord.address }
        )
      }}
      <v-list>
        <v-list-item
          v-for="result in props.mxrecord.dnsbl_results"
          :key="result.provider"
        >
          {{ result.provider }} ({{ result.status }})
        </v-list-item>
      </v-list>
    </v-card-text>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn @click="emit('close')">
        {{ $gettext('Close') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
const props = defineProps({
  mxrecord: {
    type: Object,
    default: null,
  },
})
const emit = defineEmits(['close'])
</script>
