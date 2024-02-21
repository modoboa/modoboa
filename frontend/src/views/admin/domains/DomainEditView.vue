<template>
  <div>
    <span class="text-h4">{{ $gettext('Edit domain') }}</span>
    <div class="mt-4" />
    <DomainEditForm :domain="domain" />
  </div>
</template>

<script setup lang="js">
import { useGettext } from 'vue3-gettext'
import { useDomainsStore } from '@/stores'
import DomainEditForm from '@/components/admin/domains/DomainEditForm'
import { useRoute } from 'vue-router'
import { ref } from 'vue'

const { $gettext } = useGettext()
const domainsStore = useDomainsStore()
const route = useRoute()

const domain = ref({ pk: route.params.id })

domainsStore
  .getDomain(route.params.id)
  .then((response) => (domain.value = response.data))
</script>
