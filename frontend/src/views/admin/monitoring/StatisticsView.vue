<template>
  <v-toolbar flat>
    <v-toolbar-title>{{ $gettext('Statistics') }}</v-toolbar-title>
  </v-toolbar>
  <v-layout class="pa-2">
    <v-row class="mt-2">
      <v-col cols="12">
        <TimeSerieChart
          graphic-set="mailtraffic"
          graphic-name="averagetraffic"
        />
      </v-col>
      <v-col cols="12">
        <TimeSerieChart
          graphic-set="mailtraffic"
          graphic-name="averagetrafficsize"
        />
      </v-col>
      <v-col cols="12">
        <TimeSerieChart
          graphic-set="accountgraphicset"
          graphic-name="accountcreationgraphic"
        />
      </v-col>
    </v-row>
  </v-layout>
</template>

<script setup lang="js">
import TimeSerieChart from '@/components/tools/TimeSerieChart.vue'
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
