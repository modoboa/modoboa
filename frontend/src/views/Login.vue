<template>
<v-layout align-center justify-center>
  <v-flex xs12 sm8 md4>
    <v-card class="elevation-12" @keyup.enter="authenticate">
      <v-toolbar dark color="primary">
        <v-toolbar-title>Modoboa</v-toolbar-title>
      </v-toolbar>
      <v-card-text>
        <v-text-field label="Utilisateur"
                      v-model="username"
                      :error="errors.username !== undefined"
                      :error-messages="errors.username"
                      prepend-icon="mdi-account"
                      >
        </v-text-field>
        <v-text-field label="Mot de passe"
                      type="password"
                      v-model="password"
                      :error="errors.password !== undefined"
                      :error-messages="errors.password"
                      prepend-icon="mdi-lock"
                      >
        </v-text-field>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="primary" text @click="authenticate">
          Connect
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-flex>
</v-layout>
</template>

<script>
import Cookies from 'js-cookie'
import { mapGetters } from 'vuex'

export default {
  computed: {
    ...mapGetters({
      endpoints: 'auth/endpoints'
    })
  },
  data () {
    return {
      username: '',
      password: '',
      errors: {}
    }
  },
  methods: {
    authenticate () {
      const payload = {
        username: this.username,
        password: this.password
      }
      this.$axios.post('/token/', payload).then(resp => {
        Cookies.set('token', resp.data.access, { sameSite: 'strict' })
        Cookies.set('refreshToken', resp.data.refresh, { sameSite: 'strict' })
        this.$store.dispatch('auth/initialize').then(() => {
          this.$router.push('/')
        })
      }).catch(err => {
        console.log(err)
      })
    }
  }
}
</script>
