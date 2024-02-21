<template>
    <v-toolbar flat>
        <v-toolbar-title>{{ $gettext('Forward') }}</v-toolbar-title>
    </v-toolbar>
    <div class="pa-4">
        <ForwardForm />
    </div>
</template>

<script setup lang="js">
import ForwardForm from '@/components/account/ForwardForm.vue'
</script>

<style scoped>
.v-toolbar {
    background-color: #f7f8fa !important;
}
</style>
