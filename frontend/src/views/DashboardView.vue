<template>
  <div>
    <v-toolbar flat>
      <v-toolbar-title>{{ welcomeMsg }}</v-toolbar-title>
    </v-toolbar>

    <v-row>
      <v-col sm="12" md="6">
        <NewsFeedWidget />
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import NewsFeedWidget from '@/components/admin/dashboard/NewsFeedWidget'
import parametersApi from '@/api/parameters'

const { $gettext } = useGettext()

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
