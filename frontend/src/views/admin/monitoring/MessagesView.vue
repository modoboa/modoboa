<template>
  <v-toolbar flat>
    <v-toolbar-title>{{ $gettext('Message history') }}</v-toolbar-title>
  </v-toolbar>
  <MessageList />
</template>

<script setup lang="js">
import MessageList from '@/components/admin/logs/MessageList'
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
