<template>
<v-app v-if="!isAuthenticated">
  <v-main>
    <router-view />
  </v-main>
</v-app>
<v-app v-else>
  <navbar />
  <v-main>
    <v-container fluid>
      <router-view/>
    </v-container>
  </v-main>
  <v-snackbar
    v-model="snackbar"
    :color="notificationColor"
    :timeout="notificationTimeout"
    top
    >
    {{ notification }}

    <template v-slot:action="{ attrs }">
      <v-btn
        color="white"
        text
        v-bind="attrs"
        @click="snackbar = false"
        >
        <translate>Close</translate>
      </v-btn>
    </template>
  </v-snackbar>
</v-app>
</template>

<script>
import { mapGetters } from 'vuex'
import { bus } from '@/main'
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
  created () {
    // this.$store.dispatch('auth/initialize')
    bus.$on('notification', this.showNotification)
  },
  data: () => ({
    snackbar: false,
    notification: '',
    notificationColor: 'success',
    notificationTimeout: 2000
  }),
  methods: {
    showNotification (options) {
      this.notification = options.msg
      this.notificationColor = (options.type) ? options.type : 'success'
      this.snackbar = true
    }
  }
}
</script>

<style scoped>
.v-main {
  background-color: #f7f8fa;
}
</style>
