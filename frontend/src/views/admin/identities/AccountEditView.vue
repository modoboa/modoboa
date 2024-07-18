<template>
  <v-toolbar flat>
    <v-toolbar-title>{{ $gettext('Edit account') }}</v-toolbar-title>
  </v-toolbar>
  <AccountEditForm />
</template>

<script setup lang="js">
import AccountEditForm from '@/components/admin/identities/AccountEditForm.vue'
import { useGettext } from 'vue3-gettext'

const { $gettext } = useGettext()
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
