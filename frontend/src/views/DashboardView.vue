<template>
  <v-toolbar flat>
    <v-toolbar-title>{{ $gettext('Welcome to Modoboa') }}</v-toolbar-title>
  </v-toolbar>

  <v-row>
    <v-col sm="12" md="6">
      <NewsFeedWidget />
    </v-col>
  </v-row>
</template>

<script setup>
import NewsFeedWidget from '@/components/admin/dashboard/NewsFeedWidget'
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}

.v-tabs-items {
  background-color: #f7f8fa !important;
}
</style>
