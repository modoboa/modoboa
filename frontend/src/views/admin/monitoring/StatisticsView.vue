<template>
  <v-toolbar flat color="transparent">
    <v-toolbar-title>{{ $gettext('Statistics') }}</v-toolbar-title>
  </v-toolbar>
  <v-layout class="pa-2">
    <v-row class="mt-2">
      <v-col cols="12">
        <StatisticsDomainSelect v-model="domain" />
      </v-col>
      <v-col cols="12">
        <TimeSerieChart
          :domain="domain"
          domain-required
          graphic-set="mailtraffic"
          graphic-name="averagetraffic"
        />
      </v-col>
      <v-col cols="12">
        <TimeSerieChart
          :domain="domain"
          domain-required
          graphic-set="mailtraffic"
          graphic-name="averagetrafficsize"
        />
      </v-col>
      <v-col v-if="isSuperAdmin" cols="12">
        <TimeSerieChart
          graphic-set="accountgraphicset"
          graphic-name="accountcreationgraphic"
        />
      </v-col>
    </v-row>
  </v-layout>
</template>

<script setup lang="js">
import { computed, ref } from 'vue'
import { useAuthStore } from '@/stores'
import StatisticsDomainSelect from '@/components/tools/StatisticsDomainSelect.vue'
import TimeSerieChart from '@/components/tools/TimeSerieChart.vue'
import constants from '@/constants.json'

const authStore = useAuthStore()
const domain = ref(null)
const isSuperAdmin = computed(
  () => authStore.authUser.role === constants.SUPER_ADMIN
)
</script>
