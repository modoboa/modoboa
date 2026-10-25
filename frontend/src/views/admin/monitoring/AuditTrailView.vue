<template>
  <v-toolbar flat color="transparent">
    <v-toolbar-title>{{ $gettext('Audit trail') }}</v-toolbar-title>
  </v-toolbar>
  <AuditTrailList />
</template>

<script setup lang="js">
import AuditTrailList from '@/components/admin/logs/AuditTrailList.vue'
</script>
