<template>
  <div class="text-h5 ml-4">
    {{ $gettext('Webmail') }}
  </div>
  <EmailList :mailbox="$route.query.mailbox || 'INBOX'" />
</template>

<script setup>
import EmailList from '@/components/webmail/EmailList.vue'
</script>
