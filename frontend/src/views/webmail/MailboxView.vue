<template>
  <div class="d-flex flex-column h-100">
    <EmailList :mailbox="$route.query.mailbox || 'INBOX'" />
  </div>
</template>

<script setup>
import EmailList from '@/components/webmail/EmailList.vue'
</script>
