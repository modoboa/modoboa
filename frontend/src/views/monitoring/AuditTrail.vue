<template>
<div>
  <v-toolbar flat>
    <v-toolbar-title><translate>Audit trail</translate></v-toolbar-title>
  </v-toolbar>
  <audit-trail-list />
</div>
</template>

<script>
import AuditTrailList from '@/components/logs/AuditTrailList.vue'

export default {
  components: {
    AuditTrailList
  }
}
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
