<template>
  <v-toolbar flat>
    <v-toolbar-title>{{ $gettext('Audit trail') }}</v-toolbar-title>
  </v-toolbar>
  <AuditTrailList />
</template>

<script setup lang="js">
import AuditTrailList from '@/components/admin/logs/AuditTrailList.vue'
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
