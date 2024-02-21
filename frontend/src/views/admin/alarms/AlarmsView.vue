<template>
  <v-toolbar flat>
    <v-toolbar-title>{{ $gettext('Opened alarms') }}</v-toolbar-title>
  </v-toolbar>
  <AlarmList />
</template>

<script setup lang="js">
import AlarmList from '@/components/admin/alarms/AlarmList.vue'
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
