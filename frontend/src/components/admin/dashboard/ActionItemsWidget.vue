<template>
  <v-card :title="$gettext('To do')">
    <v-card-text>
      <div v-if="!alarmCount && !dnsIssues.length" class="d-flex align-center">
        <v-icon icon="mdi-check-circle" color="success" class="mr-2" />
        {{ $gettext('Everything looks fine') }}
      </div>
      <v-list v-else density="compact">
        <template v-if="alarmCount">
          <v-list-subheader>
            {{ $gettext('Open alarms') }} ({{ alarmCount }})
          </v-list-subheader>
          <v-list-item
            v-for="alarm in alarms"
            :key="alarm.id"
            :title="alarm.title"
            :subtitle="`${alarm.domain.name} · ${$date(alarm.created)}`"
            :to="{ name: 'Alarms' }"
            prepend-icon="mdi-bell-alert"
            base-color="warning"
          />
        </template>
        <template v-if="dnsIssues.length">
          <v-list-subheader>
            {{ $gettext('Domains with DNS problems') }} ({{ dnsIssues.length }})
          </v-list-subheader>
          <v-list-item
            v-for="domain in dnsIssues"
            :key="domain.pk"
            :title="domain.name"
            :to="{ name: 'DomainDetail', params: { id: domain.pk } }"
            prepend-icon="mdi-dns"
            base-color="error"
          />
        </template>
      </v-list>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'
import alarmsApi from '@/api/alarms'
import domainsApi from '@/api/domains'
import constants from '@/constants.json'

const alarms = ref([])
const alarmCount = ref(0)
const dnsIssues = ref([])

// ponytail: walks every domain page to read dns_global_status, slow with
// thousands of domains; move to a server-side count if that becomes a problem.
const [alarmsResp, domains] = await Promise.all([
  alarmsApi.getAll({ status: constants.ALARM_OPENED, page_size: 5 }),
  domainsApi.getAllDomains(),
])
alarms.value = alarmsResp.data.results
alarmCount.value = alarmsResp.data.count
dnsIssues.value = domains.filter((d) => d.dns_global_status === 'critical')
</script>
