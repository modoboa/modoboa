<template>
  <span class="text-h4">{{ $gettext('Edit account') }}</span>
  <div class="mt-4" />
  <AccountEditForm />
</template>

<script setup lang="js">
import AccountEditForm from '@/components/admin/identities/AccountEditForm.vue'
import { useGettext } from 'vue3-gettext'

const { $gettext } = useGettext()
</script>
