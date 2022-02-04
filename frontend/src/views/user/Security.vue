<template>
<div>
  <v-toolbar flat>
    <v-toolbar-title><translate>Security</translate></v-toolbar-title>
  </v-toolbar>
  <div class="pa-4">
    <two-factor-auth-form :account="authUser" />
  </div>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import TwoFactorAuthForm from '@/components/user/TwoFactorAuthForm'

export default {
  components: {
    TwoFactorAuthForm
  },
  computed: {
    ...mapGetters({
      authUser: 'auth/authUser'
    })
  }
}
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
