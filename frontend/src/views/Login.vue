<template>
<v-row style="height: 100%; margin: 0 auto">
  <v-col cols="0" sm="6" class="primary" style="height: 100%">
    <v-img
      src="../assets/Modoboa_RVB-BLANC-SANS.png"
      max-width="300"
      class="mt-10 ml-8"
      />
  </v-col>
  <v-col cols="12" sm="6" class="d-flex flex-column justify-center pa-10" @keyup.enter="authenticate">
    <span class="primary--text mb-6 text-h4"><translate>Identification</translate></span>
    <validation-observer ref="observer">
      <validation-provider
        v-slot="{ errors }"
        rules="required"
        >
        <label class="m-label"><translate>Username</translate></label>
        <v-text-field
          v-model="username"
          :error-messages="errors"
          outlined
          />
      </validation-provider>
      <validation-provider
        vid="password"
        v-slot="{ errors }"
        rules="required"
        >
        <label class="m-label"><translate>Password</translate></label>
        <v-text-field
          type="password"
          v-model="password"
          :error-messages="errors"
          outlined
          />
      </validation-provider>
      <a href="" class="float-right primary--text"><translate>Forgot password?</translate></a>
      <v-checkbox
        v-model="rememberMe"
        :label="'Remember me'|translate"
        />
    </validation-observer>
    <div class="d-flex justify-center">
      <v-btn
        class="flex-grow-1"
        color="primary"
        large
        @click="authenticate"
        :loading="loading"
        >
        <translate>Connect</translate>
      </v-btn>
    </div>
  </v-col>
</v-row>
</template>

<script>
import Cookies from 'js-cookie'
import auth from '@/api/auth'

export default {
  data () {
    return {
      loading: false,
      rememberMe: false,
      username: '',
      password: '',
      errors: {}
    }
  },
  methods: {
    async authenticate () {
      const isValid = await this.$refs.observer.validate()
      if (!isValid) {
        return
      }
      const payload = {
        username: this.username,
        password: this.password
      }
      this.loading = true
      auth.requestToken(payload).then(resp => {
        Cookies.set('token', resp.data.access, { sameSite: 'strict' })
        Cookies.set('refreshToken', resp.data.refresh, { sameSite: 'strict' })
        this.$store.dispatch('auth/initialize').then(() => {
          this.$router.push({ name: 'DomainList' })
        })
      }).catch(err => {
        this.loading = false
        if (err.response.status === 401) {
          this.$refs.observer.setErrors({
            password: this.$gettext('Invalid username and/or password')
          })
        }
      })
    }
  }
}
</script>

<style>

</style>
