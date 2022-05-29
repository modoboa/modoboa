<template>
<div>
  <v-toolbar flat>
    <v-toolbar-title><translate>Opened alarms</translate></v-toolbar-title>
  </v-toolbar>
  <alarm-list />
</div>
</template>

<script>
import AlarmList from '@/components/alarms/AlarmList'

export default {
  components: {
    AlarmList
  }
}
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
