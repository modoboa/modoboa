<template>
<v-app v-if="!isAuthenticated">
  <v-main>
    <v-container fluid fill-height>
      <router-view />
    </v-container>
  </v-main>
</v-app>
<v-app v-else>
  <navbar />
  <v-main>
    <v-container fluid>
      <router-view/>
    </v-container>
  </v-main>
</v-app>
</template>

<script>
import { mapGetters } from 'vuex'
import Navbar from '@/components/layout/Navbar'

export default {
  name: 'App',
  computed: {
    ...mapGetters({
      isAuthenticated: 'auth/isAuthenticated'
    })
  },
  components: {
    Navbar
  },
  // created () {
  //   this.$store.dispatch('auth/initialize')
  // },
  data: () => ({
    //
  })
}
</script>

<style scoped>
.v-main {
  background-color: #f7f8fa;
}
</style>
