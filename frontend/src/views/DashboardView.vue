<template>
  <div class="dashboard">
    <v-toolbar flat color="transparent">
      <v-toolbar-title>{{ welcomeMsg }}</v-toolbar-title>
    </v-toolbar>

    <template v-if="isAdmin">
      <DashboardWidget skeleton="heading">
        <GlobalStatisticsWidget />
      </DashboardWidget>
      <v-row>
        <v-col cols="12" md="8">
          <DashboardWidget>
            <ActionItemsWidget />
          </DashboardWidget>
          <template v-if="isSuperAdmin">
            <TimeSerieChart
              class="mt-4"
              graphic-set="mailtraffic"
              graphic-name="averagetraffic"
            />
            <DashboardWidget>
              <RecentActivityWidget class="mt-4" />
            </DashboardWidget>
          </template>
        </v-col>
        <v-col cols="12" md="4">
          <DashboardWidget v-if="isSuperAdmin">
            <SystemStatusWidget class="mb-4" />
          </DashboardWidget>
          <DashboardWidget>
            <NewsFeedWidget />
          </DashboardWidget>
        </v-col>
      </v-row>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useAuthStore } from '@/stores'

import ActionItemsWidget from '@/components/admin/dashboard/ActionItemsWidget'
import DashboardWidget from '@/components/admin/dashboard/DashboardWidget'
import GlobalStatisticsWidget from '@/components/admin/dashboard/GlobalStatisticsWidget'
import NewsFeedWidget from '@/components/admin/dashboard/NewsFeedWidget'
import RecentActivityWidget from '@/components/admin/dashboard/RecentActivityWidget'
import SystemStatusWidget from '@/components/admin/dashboard/SystemStatusWidget'
import TimeSerieChart from '@/components/tools/TimeSerieChart.vue'
import parametersApi from '@/api/parameters'
import constants from '@/constants.json'

const { $gettext } = useGettext()
const authStore = useAuthStore()

const welcomeMsg = ref('')
const isAdmin = computed(() => authStore.authUser.role !== constants.USER)
const isSuperAdmin = computed(
  () => authStore.authUser.role === constants.SUPER_ADMIN
)

onMounted(async () => {
  const response = await parametersApi.getGlobalApplication('core')
  if (response.data.params.custom_welcome_message) {
    welcomeMsg.value = response.data.params.custom_welcome_message
  } else {
    welcomeMsg.value = $gettext('Welcome to Modoboa')
  }
})
</script>

<style scoped>
.dashboard :deep(.v-card) {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
}
</style>
