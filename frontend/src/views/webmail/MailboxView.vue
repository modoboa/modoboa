<template>
  <div class="d-flex flex-column h-100">
    <div class="text-headline-medium ml-4">
      {{ $gettext('Webmail') }}
    </div>
    <EmailList :mailbox="$route.query.mailbox || 'INBOX'" />
  </div>
</template>

<script setup>
import EmailList from '@/components/webmail/EmailList.vue'
</script>
