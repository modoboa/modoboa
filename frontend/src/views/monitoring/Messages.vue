<template>
<div>
  <v-toolbar flat>
    <v-toolbar-title><translate>Message history</translate></v-toolbar-title>
  </v-toolbar>
  <message-list />
</div>
</template>

<script>
import MessageList from '@/components/logs/MessageList'

export default {
  components: {
    MessageList
  }
}
</script>
