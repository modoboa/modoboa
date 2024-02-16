<template>
  <div>
    <span class="text-h4"> {{ $gettext('Edit provider') }} </span>
    <div class="mt-4" />
    <ProviderForm :provider="provider" />
  </div>
</template>

<script setup lang="js">
import providersApi from '@/api/imap_migration/providers'
import ProviderForm from '@/components/admin/imap_migration/ProviderForm.vue'
import { ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useRoute } from 'vue-router'

const { $gettext } = useGettext()
const route = useRoute()

const provider = ref({})

providersApi.getProvider(route.params.id).then((response) => {
  provider.value = response.data
})
</script>
