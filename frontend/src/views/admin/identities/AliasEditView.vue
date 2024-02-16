<template>
  <div>
    <span class="text-h4">{{ $gettext('Edit alias') }}</span>
    <div class="mt-4" />
    <AliasEditForm :alias="alias" />
  </div>
</template>

<script setup lang="js">
import AliasEditForm from '@/components/admin/identities/AliasEditForm.vue'
import { useGettext } from 'vue3-gettext'

const { $gettext } = useGettext()
</script>
