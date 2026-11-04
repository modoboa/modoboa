<template>
  <v-card :title="$gettext('Recent activity')">
    <v-card-text>
      <v-list density="compact">
        <v-list-item
          v-for="(log, index) in logs"
          :key="index"
          :title="log.action_label || log.message"
          :subtitle="getSubtitle(log)"
          :prepend-icon="getLevelIcon(log.level)"
          :base-color="getLevelColor(log.level)"
        />
      </v-list>
    </v-card-text>
    <v-card-actions class="justify-center">
      <v-btn :to="{ name: 'AuditTrail' }" variant="text" color="primary">
        {{ $gettext('See full audit trail') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'
import logsApi from '@/api/logs'

const logs = ref([])

function getLevelColor(level) {
  if (level === 'WARNING') {
    return 'warning'
  }
  if (level === 'CRITICAL' || level === 'ERROR') {
    return 'error'
  }
  return undefined
}

function getSubtitle(log) {
  if (!log.action) {
    return `${log.date_created} · ${log.logger}`
  }
  return [log.object_repr, log.actor_name, log.date_created]
    .filter(Boolean)
    .join(' · ')
}

function getLevelIcon(level) {
  return getLevelColor(level) ? 'mdi-alert' : 'mdi-information-outline'
}

const resp = await logsApi.getAuditTrail({ page_size: 5 })
logs.value = resp.data.results
</script>
