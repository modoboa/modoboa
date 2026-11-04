<template>
  <v-card :title="$gettext('Recent activity')">
    <v-card-text>
      <v-list density="compact">
        <v-list-item
          v-for="(log, index) in logs"
          :key="index"
          :title="getTitle(log)"
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
import { formatDate } from '@/plugins/filters'
import { getAuditDetails } from '@/utils/audit'

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

function getTitle(log) {
  return [formatDate(log.date_created), log.action_label, log.actor_name]
    .filter(Boolean)
    .join(' · ')
}

function getSubtitle(log) {
  // Entries written before structured fields existed only have a message
  return log.action ? getAuditDetails(log) : log.message
}

function getLevelIcon(level) {
  return getLevelColor(level) ? 'mdi-alert' : 'mdi-information-outline'
}

const resp = await logsApi.getAuditTrail({ page_size: 5 })
logs.value = resp.data.results
</script>
