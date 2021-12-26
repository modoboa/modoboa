<template>
<div>
  <v-toolbar flat>
    <v-toolbar-title><translate>Profile</translate></v-toolbar-title>
  </v-toolbar>
  <div class="pa-4">
    <profile-form :account="authUser" />
  </div>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import ProfileForm from '@/components/user/ProfileForm'

export default {
  components: {
    ProfileForm
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
