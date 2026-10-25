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
        <v-col cols="12" md="6">
          <DashboardWidget>
            <ActionItemsWidget />
          </DashboardWidget>
        </v-col>
        <v-col cols="12" md="6">
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
import parametersApi from '@/api/parameters'
import constants from '@/constants.json'

const { $gettext } = useGettext()
const authStore = useAuthStore()

const welcomeMsg = ref('')
const isAdmin = computed(() => authStore.authUser.role !== constants.USER)

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
