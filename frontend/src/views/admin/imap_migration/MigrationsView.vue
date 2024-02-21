<template>
  <div>
    <v-toolbar flat>
      <v-toolbar-title>{{ $gettext('Migrations') }}</v-toolbar-title>
      <v-spacer />
    </v-toolbar>

    <MigrationsList />
  </div>
</template>

<script setup lang="js">
import { useGettext } from 'vue3-gettext'
import MigrationsList from '@/components/admin/imap_migration/MigrationsList.vue'

const { $gettext } = useGettext()
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}

.v-tabs-items {
  background-color: #f7f8fa !important;
}
</style>
