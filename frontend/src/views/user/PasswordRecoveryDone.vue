<template>
  <v-row style="height: 100%; margin: 0 auto">
    <v-col cols="0" sm="6" class="primary" style="height: 100%">
      <v-img
        src="../../assets/Modoboa_RVB-BLANC-SANS.png"
        max-width="300"
        class="mt-10 ml-8"
        />
    </v-col>
    <v-col v-if="this.fail">
      <div>
        <p>There was an error</p>
      </div>
    </v-col>
    <v-col v-else>
      <div>
        <p>Everything alright</p>
      </div>
    </v-col>
>    <v-col>
      <div>
        <a @click="returnLogin" class="float-right primary--text"><translate>Return to login?</translate></a>
      </div>
    </v-col>
  </v-row>
</template>

<script>
import auth from '@/api/auth'

export default {
  data () {
    return {
      fail: true
    }
  },
  methods: {
    returnLogin () {
      this.$router.push({ name: 'Login' })
    },
    async recoverPassword () {
      const isValid = await this.$refs.observer.validate()
      if (!isValid) {
        return
      }
      const payload = {
        password: this.password
      }
      this.loading = true
      auth.recoverPassword(payload).then(resp => {
        console.log('ok')
      }).catch(err => {
        this.loading = false
        if (err.response.status === 400) {
          this.$refs.observer.setErrors({
            email: this.$gettext('Invalid email')
          })
        }
      })
    }
  }
}
</script>

<style>
</style>
