<template>
  <template v-if="smAndDown">
    <PasswordRecoverySmsTotpForm />
  </template>
  <template v-else>
    <v-row class="fill-height ma-0">
      <v-col class="bg-primary">
        <v-img
          src="@/assets/Modoboa_RVB-BLANC-SANS.png"
          max-width="300"
          class="mt-10 ml-8"
        />
      </v-col>
      <v-col class="text-center">
        <PasswordRecoverySmsTotpForm />
      </v-col>
    </v-row>
  </template>
</template>

<script setup lang="js">
import PasswordRecoverySmsTotpForm from '@/components/login/PasswordRecoverySmsTotpForm.vue'
import { useDisplay } from 'vuetify'

const { smAndDown } = useDisplay()
</script>
