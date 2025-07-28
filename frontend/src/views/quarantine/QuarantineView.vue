<template>
  <div class="text-h5 ml-4">
    {{ $gettext('Quarantine') }}
  </div>

  <QuarantineList />
</template>

<script setup>
import QuarantineList from '@/components/quarantine/QuarantineList'
</script>
