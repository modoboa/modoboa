<template>
<v-toolbar flat>
  <v-toolbar-title>{{ $gettext('Account settings') }}</v-toolbar-title>
</v-toolbar>
<div class="pa-4">
  <v-tabs
    v-model="tab"
    color="primary"
    class="mb-4"
  >
    <v-tab value="profile">
      {{ $gettext('Profile') }}
    </v-tab>
    <v-tab value="security">
      {{ $gettext('Security') }}
    </v-tab>
    <v-tab value="forward" v-if="authStore.userHasMailbox">
      {{ $gettext('Forward') }}
    </v-tab>
    <v-tab value="autoreply" v-if="authStore.userHasMailbox">
      {{ $gettext('Auto-reply message') }}
    </v-tab>
    <v-tab value="api" v-if="authStore.authUser.role === 'SuperAdmins'">
      {{ $gettext('API access') }}
    </v-tab>
  </v-tabs>
  <v-window v-model="tab">
    <v-window-item value="profile">
      <ProfileForm />
    </v-window-item>
    <v-window-item value="security">
      <TwoFactorAuthForm />
    </v-window-item>
    <v-window-item value="forward" v-if="authStore.userHasMailbox">
      <ForwardForm />
    </v-window-item>
    <v-window-item value="autoreply" v-if="authStore.userHasMailbox">
      <AutoReplyForm />
    </v-window-item>
    <v-window-item value="api" v-if="authStore.authUser.role === 'SuperAdmins'">
      <APISetupForm />
    </v-window-item>
  </v-window>
</div>
</template>

<script setup>
import { ref } from 'vue'
import ProfileForm from '@/components/account/ProfileForm.vue'
import TwoFactorAuthForm from '@/components/account/TwoFactorAuthForm.vue'
import ForwardForm from '@/components/account/ForwardForm.vue'
import AutoReplyForm from '@/components/account/AutoReplyForm.vue'
import APISetupForm from '@/components/account/APISetupForm.vue'
import { useAuthStore } from '@/stores'

const authStore = useAuthStore()
const tab = ref()
</script>

<style scoped>
 .v-toolbar {
   background-color: #f7f8fa !important;
 }
 .v-tabs {
   background-color: #f7f8fa !important;
 }
</style>
