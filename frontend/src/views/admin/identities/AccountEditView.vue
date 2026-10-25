<template>
  <v-toolbar flat color="transparent">
    <v-toolbar-title>{{ $gettext('Edit account') }}</v-toolbar-title>
  </v-toolbar>
  <AccountEditForm />
</template>

<script setup lang="js">
import AccountEditForm from '@/components/admin/identities/AccountEditForm.vue'
import { useGettext } from 'vue3-gettext'

const { $gettext } = useGettext()
</script>
