<template>
<v-card>
  <v-toolbar dense elevation="0">
    <v-toolbar-title>{{ title }}</v-toolbar-title>
    <v-spacer />
    <v-menu
      v-model="menu"
      :nudge-width="200"
      offset-y
    >
      <template v-slot:activator="{ on, attrs }">
        <v-btn
          small
          v-bind="attrs"
          v-on="on"
          >
          <v-icon small>mdi-calendar</v-icon>
          <translate>Period</translate>
          <span v-if="period">: {{ period }}</span>
        </v-btn>
      </template>
      <v-layout>
        <v-row>
          <v-col cols="6" class="d-flex flex-column align-start py-3 px-6">
            <translate class="subtitle">Absolute time range</translate>
            <date-field v-model="start" :label="'From'|translate" />
            <date-field v-model="end" :label="'To'|translate" />
            <v-btn color="primary" @click="setCustomPeriod"><translate>Apply</translate></v-btn>
          </v-col>
          <v-col cols="6">
            <translate class="subtitle">Relative time ranges</translate>
            <v-list>
              <v-list-item
                v-for="period in periods"
                :key="period.value"
                @click="setPeriod(period.value)"
                >
                <v-list-item-title>{{ period.name }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-col>
        </v-row>
      </v-layout>
    </v-menu>
  </v-toolbar>
  <v-card-text>
    <apexchart
      v-if="statistics"
      type="area"
      height="350"
      :options="options"
      :series="statistics.series"
      />
  </v-card-text>
</v-card>
</template>

<script>
import VueApexCharts from 'vue-apexcharts'
import statistics from '@/api/statistics'
import DateField from './DateField'

export default {
  components: {
    apexchart: VueApexCharts,
    DateField
  },
  props: ['domain', 'graphicSet', 'graphicName'],
  computed: {
    title () {
      if (this.statistics) {
        return this.statistics.title
      }
      return ''
    }
  },
  data () {
    return {
      dateMenu: false,
      menu: false,
      options: {
        colors: [],
        chart: {
          type: 'area',
          stacked: false,
          zoom: {
            type: 'x',
            enabled: true,
            autoScaleYaxis: true
          },
          toolbar: {
            autoSelected: 'zoom'
          }
        },
        dataLabels: {
          enabled: false
        },
        yaxis: {
        },
        xaxis: {
          type: 'datetime'
        }
      },
      end: null,
      start: null,
      statistics: null,
      period: 'day',
      periods: [
        { value: 'day', name: this.$gettext('Day') },
        { value: 'week', name: this.$gettext('Week') },
        { value: 'month', name: this.$gettext('Month') },
        { value: 'year', name: this.$gettext('Year') }
      ]
    }
  },
  methods: {
    getColors () {
      if (this.graphicName === 'averagetraffic') {
        return ['#ff6347', '#ffff00', '#4682B4', '#7cfc00', '#ffa500', '#d3d3d3']
      }
      return ['#ffa500', '#41d1cc']
    },
    setCustomPeriod () {
      this.period = 'custom'
      this.fetchStatistics()
    },
    setPeriod (period) {
      if (period !== this.period) {
        this.period = period
        this.fetchStatistics()
      }
    },
    fetchStatistics () {
      const args = {
        graphSet: this.graphicSet,
        period: this.period,
        graphicName: this.graphicName,
        searchQuery: this.domain.name
      }
      if (this.period === 'custom') {
        args.start = this.start
        args.end = this.end
      }
      statistics.getStatistics(args).then(resp => {
        this.statistics = resp.data.graphs[this.graphicName]
      })
    }
  },
  mounted () {
    this.fetchStatistics()
  },
  watch: {
    graphicName (newValue) {
      this.$set(this.options, 'colors', this.getColors())
    }
  }
}
</script>

<style scoped>
.v-card {
  z-index: 5;
}
.v-menu__content {
  background-color: white !important;
}
</style>
