<template>
  <div>
    <v-toolbar flat>
      <v-toolbar-title>{{ welcomeMsg }}</v-toolbar-title>
    </v-toolbar>

    <v-row>
      <v-col sm="12" md="6">
        <NewsFeedWidget />
        <GlobalStatisticsWidget
          v-if="authStore.authUser.role === constants.SUPER_ADMIN"
          class="mt-4"
        />
      </v-col>
      <v-col sm="12" md="6"> </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useAuthStore } from '@/stores'

import GlobalStatisticsWidget from '@/components/admin/dashboard/GlobalStatisticsWidget'
import NewsFeedWidget from '@/components/admin/dashboard/NewsFeedWidget'
import parametersApi from '@/api/parameters'
import constants from '@/constants.json'

const { $gettext } = useGettext()
const authStore = useAuthStore()

const welcomeMsg = ref('')

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
.v-toolbar {
  background-color: #f7f8fa !important;
}

.v-tabs-items {
  background-color: #f7f8fa !important;
}
</style>
