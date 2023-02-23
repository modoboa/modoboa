<template>
<div v-if="alignments">
  <v-card>
    <v-toolbar dense elevation="0" class="mr-2">
      <v-toolbar-title><translate>Alignment</translate></v-toolbar-title>
      <v-spacer />
      <v-btn
        icon
        x-small
        @click="previousWeek"
        >
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <span class="mx-2">{{ weekStart.toLocaleString() }} - {{ weekEnd.toLocaleString() }}</span>
      <v-btn
        icon
        x-small
        @click="nextWeek"
        >
        <v-icon>mdi-arrow-right</v-icon>
      </v-btn>
    </v-toolbar>
    <v-card-text>
      <v-row>
        <v-col cols="5">
          <apexchart
            v-if="series"
            type="pie"
            height="350"
            :options="options"
            :series="series"
            />
        </v-col>
        <v-col cols="7">
          <v-row>
            <v-col
              v-for="box in boxes"
              :key="box.key"
              cols="6"
              >
              <v-sheet
                outlined
                :color="box.color"
                rounded
                >
                <v-card
                  outlined
                  class="pa-10 text-center"
                  >
                  <span :class="'text-h4 ' + getTextColors(box.color)">{{ stats[box.key] }}</span><br>
                  <span class="text-subtitle-1">{{ box.label }}</span>
                </v-card>
              </v-sheet>
            </v-col>
          </v-row>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
  <v-expansion-panels
    v-model="panel"
    class="mt-2"
    >
    <v-expansion-panel>
      <v-expansion-panel-header>
        <translate>Detail</translate>
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <dmarc-source-table
          :title="'Trusted sources'|translate"
          color="green"
          :total="stats.aligned"
          :sources="alignments.aligned"
          />
        <dmarc-source-table
          :title="'Partially trusted sources / Forwarders'|translate"
          color="orange"
          :total="stats.trusted"
          :sources="alignments.trusted"
          class="mt-4"
          />
        <dmarc-source-table
          :title="'Forwarders with ARC'|translate"
          color="blue"
          :total="stats.forwarded"
          :sources="alignments.forwarded"
          class="mt-4"
          />
        <dmarc-source-table
          :title="'Unknown sources / Threats'|translate"
          color="red"
          :total="stats.failed"
          :sources="alignments.failed"
          class="mt-4"
          />
      </v-expansion-panel-content>
    </v-expansion-panel>
  </v-expansion-panels>
</div>
<div v-else>
  <v-alert
    v-if="dmarcDisabled"
    type="info"
    outlined
    prominent
    border="left"
    class="mt-6"
    >
    <translate tag="div">
      DMARC support does not seem to be enabled for this domain.</translate>
    <translate tag="div">
      If you configured it recently, please wait for the first report to be received and processed.
    </translate>
  </v-alert>
</div>
</template>

<script>
import colors from 'vuetify/lib/util/colors'
import DmarcSourceTable from './DmarcSourceTable'
import domainsApi from '@/api/domains'
import { DateTime } from 'luxon'
import VueApexCharts from 'vue-apexcharts'

const order = ['aligned', 'trusted', 'forwarded', 'failed']

export default {
  components: {
    apexchart: VueApexCharts,
    DmarcSourceTable
  },
  props: {
    domain: Object
  },
  data () {
    return {
      options: {
        colors: [colors.green.lighten2, colors.orange.lighten2, colors.blue.lighten2, colors.red.lighten2],
        labels: [
          this.$gettext('Fully aligned'),
          this.$gettext('Partially aligned'),
          this.$gettext('Forwarded'),
          this.$gettext('Failed')
        ],
        legend: {
          position: 'bottom'
        }
      },
      alignments: null,
      boxes: [
        { key: 'total', label: this.$gettext('Total'), color: 'primary lighten-2' },
        { key: 'aligned', label: this.$gettext('Fully aligned'), color: 'green lighten-2' },
        { key: 'trusted', label: this.$gettext('Partially aligned'), color: 'orange lighten-2' },
        { key: 'forwarded', label: this.$gettext('Forwarded'), color: 'blue lighten-2' },
        { key: 'failed', label: this.$gettext('Failed'), color: 'red lighten-2' }
      ],
      currentWeek: 0,
      currentYear: 0,
      dmarcDisabled: false,
      loading: false,
      panel: null,
      series: [],
      stats: {}
    }
  },
  computed: {
    weekStart () {
      const dt = DateTime.fromObject({
        weekYear: this.currentYear,
        weekNumber: this.currentWeek
      })
      return dt.startOf('week')
    },
    weekEnd () {
      const dt = DateTime.fromObject({
        weekYear: this.currentYear,
        weekNumber: this.currentWeek
      })
      return dt.endOf('week')
    }
  },
  methods: {
    getTextColors (value) {
      let result = ''
      for (const color of value.split(' ')) {
        if (result !== '') {
          result += ' '
        }
        if (color.startsWith('lighten')) {
          result += 'text--' + color
        } else {
          result += color + '--text'
        }
      }
      return result
    },
    nextWeek () {
      if (this.currentWeek === 52) {
        this.currentYear += 1
        this.currentWeek = 1
      } else {
        this.currentWeek += 1
      }
    },
    previousWeek () {
      if (this.currentWeek === 1) {
        this.currentYear -= 1
        this.currentWeek = 52
      } else {
        this.currentWeek -= 1
      }
    },
    fetchAlignmentStats () {
      if (this.loading) {
        return
      }
      const period = `${this.currentYear}-${this.currentWeek}`
      this.loading = true
      domainsApi.getDomainDmarcAlignment(this.domain.pk, period).then(resp => {
        this.loading = false
        if (resp.status === 204) {
          this.dmarcDisabled = true
          return
        }
        this.stats = { total: 0 }
        this.alignments = resp.data
        this.series = []
        for (const key of order) {
          let total = 0
          for (const name in resp.data[key]) {
            for (const ip in resp.data[key][name]) {
              total += resp.data[key][name][ip].total
            }
          }
          this.stats.total += total
          this.stats[key] = total
          this.series.push(total)
        }
      })
    }
  },
  created () {
    const now = DateTime.now()
    this.currentYear = now.year
    this.currentWeek = now.weekNumber
  },
  mounted () {
    this.fetchAlignmentStats()
  },
  watch: {
    currentWeek () {
      this.fetchAlignmentStats()
    },
    currentYear () {
      this.fetchAlignmentStats()
    }
  }
}
</script>
