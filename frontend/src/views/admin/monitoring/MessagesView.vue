<template>
  <v-toolbar flat color="transparent">
    <v-toolbar-title>{{ $gettext('Message history') }}</v-toolbar-title>
  </v-toolbar>
  <MessageList />
</template>

<script setup lang="js">
import MessageList from '@/components/admin/logs/MessageList'
</script>
