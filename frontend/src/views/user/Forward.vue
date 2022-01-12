<template>
<div>
  <v-toolbar flat>
    <v-toolbar-title><translate>Forward</translate></v-toolbar-title>
  </v-toolbar>
  <div class="pa-4">
    <forward-form :account="authUser" />
  </div>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import ForwardForm from '@/components/user/ForwardForm'

export default {
  components: {
    ForwardForm
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
