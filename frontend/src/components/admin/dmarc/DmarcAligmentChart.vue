<template>
  <div v-if="alignments">
    <v-card>
      <v-toolbar dense elevation="0" class="mr-2">
        <v-toolbar-title>{{ $gettext('Alignment') }}</v-toolbar-title>
        <v-spacer />
        <v-btn icon="mdi-arrow-left" size="x-small" @click="previousWeek">
        </v-btn>
        <span class="mx-2"
          >{{ weekStart.toLocaleString() }} -
          {{ weekEnd.toLocaleString() }}</span
        >
        <v-btn icon="mdi-arrow-right" size="x-small" @click="nextWeek"> </v-btn>
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
              <v-col v-for="box in boxes" :key="box.key" cols="6">
                <v-sheet outlined :color="box.color" rounded>
                  <v-card outlined class="pa-10 text-center">
                    <span :class="'text-h4 ' + getTextColors(box.color)">{{
                      stats[box.key]
                    }}</span
                    ><br />
                    <span class="text-subtitle-1">{{ box.label }}</span>
                  </v-card>
                </v-sheet>
              </v-col>
            </v-row>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
    <v-expansion-panels v-model="panel" class="mt-2">
      <v-expansion-panel :title="$gettext('Detail')">
        <v-expansion-panel-text>
          <DmarcSourceTable
            :title="$gettext('Trusted sources')"
            color="green"
            :total="stats.aligned"
            :sources="alignments.aligned"
          />
          <DmarcSourceTable
            :title="$gettext('Partially trusted sources / Forwarders')"
            color="orange"
            :total="stats.trusted"
            :sources="alignments.trusted"
            class="mt-4"
          />
          <DmarcSourceTable
            :title="$gettext('Forwarders with ARC')"
            color="blue"
            :total="stats.forwarded"
            :sources="alignments.forwarded"
            class="mt-4"
          />
          <DmarcSourceTable
            :title="$gettext('Unknown sources / Threats')"
            color="red"
            :total="stats.failed"
            :sources="alignments.failed"
            class="mt-4"
          />
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
  </div>
  <div v-else>
    <v-alert
      v-if="dmarcDisabled"
      type="info"
      variant="outlined"
      prominent
      border="start"
      class="mt-6"
    >
      <div>
        {{
          $gettext('DMARC support does not seem to be enabled for this domain.')
        }}
      </div>
      <div>
        {{
          $gettext(
            'If you configured it recently, please wait for the first report to be received and processed.'
          )
        }}
      </div>
    </v-alert>
  </div>
</template>

<script setup lang="js">
import colors from 'vuetify/lib/util/colors'
import DmarcSourceTable from './DmarcSourceTable.vue'
import domainsApi from '@/api/domains'
import { useGettext } from 'vue3-gettext'
import { DateTime } from 'luxon'
import { ref, computed, onMounted, watch } from 'vue'

const { $gettext } = useGettext()

const order = ['aligned', 'trusted', 'forwarded', 'failed']

const props = defineProps({
  domain: { type: Object, default: () => null },
})

const options = ref({
  colors: [
    colors.green.lighten2,
    colors.orange.lighten2,
    colors.blue.lighten2,
    colors.red.lighten2,
  ],
  labels: [
    $gettext('Fully aligned'),
    $gettext('Partially aligned'),
    $gettext('Forwarded'),
    $gettext('Failed'),
  ],
  legend: {
    position: 'bottom',
  },
})

const alignments = ref(null)

const boxes = ref([
  { key: 'total', label: $gettext('Total'), color: 'primary lighten-2' },
  {
    key: 'aligned',
    label: $gettext('Fully aligned'),
    color: 'green lighten-2',
  },
  {
    key: 'trusted',
    label: $gettext('Partially aligned'),
    color: 'orange lighten-2',
  },
  { key: 'forwarded', label: $gettext('Forwarded'), color: 'blue lighten-2' },
  { key: 'failed', label: $gettext('Failed'), color: 'red lighten-2' },
])

const now = DateTime.now()
const currentYear = ref(now.year)
const currentWeek = ref(now.weekNumber)
const dmarcDisabled = ref(false)
const loading = ref(false)
const panel = ref(null)
const series = ref([])
const stats = ref({})

const weekStart = computed(() => {
  const dt = DateTime.fromObject({
    weekYear: currentYear.value,
    weekNumber: currentWeek.value,
  })
  return dt.startOf('week')
})

const weekEnd = computed(() => {
  const dt = DateTime.fromObject({
    weekYear: currentYear.value,
    weekNumber: currentWeek.value,
  })
  return dt.endOf('week')
})

function getTextColors(value) {
  let result = ''
  for (const color of value.split(' ')) {
    if (result !== '') {
      result += ' '
    }
    result += 'text-' + color
  }
  return result
}

function nextWeek() {
  if (currentWeek.value === 52) {
    currentYear.value += 1
    currentWeek.value = 1
  } else {
    currentWeek.value += 1
  }
}
function previousWeek() {
  if (currentWeek.value === 1) {
    currentYear.value -= 1
    currentWeek.value = 52
  } else {
    currentWeek.value -= 1
  }
}
function fetchAlignmentStats() {
  if (loading.value) {
    return
  }

  const period = `${currentYear.value}-${currentWeek.value}`
  loading.value = true
  domainsApi.getDomainDmarcAlignment(props.domain.pk, period).then((resp) => {
    loading.value = false
    if (resp.status === 204) {
      dmarcDisabled.value = true
      return
    }
    stats.value = { total: 0 }
    alignments.value = resp.data
    series.value = []
    for (const key of order) {
      let total = 0
      for (const name in resp.data[key]) {
        for (const ip in resp.data[key][name]) {
          total += resp.data[key][name][ip].total
        }
      }
      stats.value.total += total
      stats.value[key] = total
      series.value.push(total)
    }
  })
}
onMounted(() => fetchAlignmentStats())

watch(currentWeek, () => {
  fetchAlignmentStats()
})

watch(currentYear, () => {
  fetchAlignmentStats()
})
</script>
