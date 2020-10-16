<template>
<v-app v-if="!isAuthenticated">
  <v-main>
    <v-container fluid fill-height>
      <router-view />
    </v-container>
  </v-main>
</v-app>
<v-app v-else>
  <topbar />
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
import Topbar from '@/components/layout/Topbar'

export default {
  name: 'App',
  computed: {
    ...mapGetters({
      isAuthenticated: 'auth/isAuthenticated'
    })
  },
  components: {
    Navbar,
    Topbar
  },
  // created () {
  //   this.$store.dispatch('auth/initialize')
  // },
  data: () => ({
    //
  })
}
</script>
