<template>
  <v-toolbar flat>
    <v-toolbar-title>{{ $gettext('Edit domain') }}</v-toolbar-title>
  </v-toolbar>
  <DomainEditForm :domain="domain" />
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

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
