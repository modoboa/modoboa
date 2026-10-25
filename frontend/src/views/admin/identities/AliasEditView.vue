<template>
  <v-toolbar flat color="transparent">
    <v-toolbar-title>{{ $gettext('Edit alias') }}</v-toolbar-title>
  </v-toolbar>
  <AliasEditForm />
</template>

<script setup lang="js">
import AliasEditForm from '@/components/admin/identities/AliasEditForm.vue'
import { useGettext } from 'vue3-gettext'

const { $gettext } = useGettext()
</script>
