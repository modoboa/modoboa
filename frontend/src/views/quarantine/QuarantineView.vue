<template>
  <div>
    <div class="text-h5 ml-4">
      {{ $gettext('Quarantine') }}
      <v-chip
        v-if="route.query.requests === '1'"
        color="primary"
        variant="tonal"
        class="ml-2"
        closable
        @click:close="showAllContent"
        >{{ $gettext('release requests') }}</v-chip
      >
    </div>

    <QuarantineList />
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import QuarantineList from '@/components/quarantine/QuarantineList'

const route = useRoute()
const router = useRouter()

const showAllContent = () => {
  router.replace({ name: 'QuarantineView' })
}
</script>
