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
import alarms from '@/api/alarms'
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
    bus.$on('logged', this.checkAlarms)
  },
  mounted () {
    this.checkAlarms()
  },
  beforeDestroy () {
    clearInterval(this.alarmChecker)
  },
  data: () => ({
    snackbar: false,
    notification: '',
    notificationColor: 'success',
    notificationTimeout: 2000,
    alarmNotified: [],
    alarmChecker: null
  }),
  methods: {
    showNotification (options) {
      if (this.isAuthenticated) {
        this.notification = options.msg
        this.notificationColor = (options.type) ? options.type : 'success'
        this.snackbar = true
      }
    },
    checkAlarms () {
      if (this.isAuthenticated) {
        this.alarmChecker = window.setInterval(() => {
          alarms.getAll({}).then(resp => {
            let count = 0
            for (const alarm of resp.data) {
              if (alarm.status === 1 && !this.alarmNotified.includes(alarm.id)) {
                count++
                this.alarmNotified.push(alarm.id)
              }
            }
            if (count !== 0) {
              bus.$emit('notification', { msg: this.$gettext('You have one or more opened alarms'), type: 'error' })
            }
          })
        }, 10000)
      }
    }
  }
}
</script>

<style scoped>
.v-main {
  background-color: #f7f8fa;
}
</style>
