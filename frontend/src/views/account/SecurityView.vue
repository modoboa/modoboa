<template>
    <div>
        <v-toolbar flat>
            <v-toolbar-title>{{ $gettext('Security') }}</v-toolbar-title>
        </v-toolbar>
        <div class="pa-4">
            <TwoFactorAuthForm />
        </div>
    </div>
</template>

<script setup lang="js">
import TwoFactorAuthForm from '@/components/account/TwoFactorAuthForm.vue'
import { useGettext } from 'vue3-gettext'

const { $gettext } = useGettext()
</script>

<style scoped>
.v-toolbar {
    background-color: #f7f8fa !important;
}
</style>
