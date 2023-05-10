<template>
<div>
  <v-toolbar flat>
    <v-toolbar-title><translate>Statistics</translate></v-toolbar-title>
  </v-toolbar>
  <v-layout class="pa-2">
    <v-row class="mt-2">
      <v-col cols="12">
        <time-serie-chart
          graphic-set="mailtraffic"
          graphic-name="averagetraffic"
          />
      </v-col>
      <v-col cols="12">
        <time-serie-chart
          graphic-set="mailtraffic"
          graphic-name="averagetrafficsize"
          />
      </v-col>
      <v-col cols="12">
        <time-serie-chart
          graphic-set="accountgraphicset"
          graphic-name="accountcreationgraphic"
          />
      </v-col>
    </v-row>
  </v-layout>
</div>
</template>

<script>
import TimeSerieChart from '@/components/tools/TimeSerieChart'

export default {
  components: {
    TimeSerieChart
  }
}
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
