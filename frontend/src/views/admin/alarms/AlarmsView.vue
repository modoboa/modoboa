<template>
  <div>
    <v-toolbar flat color="transparent">
      <v-toolbar-title>{{ $gettext('Opened alarms') }}</v-toolbar-title>
    </v-toolbar>
    <AlarmList />
  </div>
</template>

<script setup lang="js">
import AlarmList from '@/components/admin/alarms/AlarmList.vue'
</script>
