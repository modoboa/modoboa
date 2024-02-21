<template>
    <div>
        <v-toolbar flat>
            <v-toolbar-title>{{ $gettext('Profile') }}</v-toolbar-title>
        </v-toolbar>
        <div class="pa-4">
            <ProfileForm />
        </div>
    </div>
</template>

<script setup lang="js">
import ProfileForm from '@/components/account/ProfileForm.vue'
import { useGettext } from 'vue3-gettext'

const { $gettext } = useGettext()
</script>

<style scoped>
.v-toolbar {
    background-color: #f7f8fa !important;
}
</style>
