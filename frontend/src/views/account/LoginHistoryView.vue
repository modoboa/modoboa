<template>
  <div>
    <v-toolbar flat color="transparent">
      <v-toolbar-title>{{ $gettext('Recent logins') }}</v-toolbar-title>
    </v-toolbar>
    <div class="pa-4">
      <LoginHistory />
    </div>
  </div>
</template>

<script setup>
import LoginHistory from '@/components/account/LoginHistory.vue'
</script>
