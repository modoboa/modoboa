<template>
  <v-toolbar flat>
    <v-toolbar-title>{{ $gettext('Edit domain') }}</v-toolbar-title>
  </v-toolbar>
  <DomainEditForm :domain="domain" />
</template>

<script setup lang="js">
import { useGettext } from 'vue3-gettext'
import DomainEditForm from '@/components/admin/domains/DomainEditForm'
import { useRoute } from 'vue-router'
import { ref } from 'vue'
import domainsApi from '@/api/domains'
import { useDomainsStore } from '@/stores'

const { $gettext } = useGettext()
const route = useRoute()
const domainsStore = useDomainsStore()

const domain = ref({})

domainsStore.getDomains()
domainsApi.getDomain(route.params.id).then((resp) => {
  domain.value = resp.data
})
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
