<template>
  <v-card>
    <v-card-title>
      <span class="headline"> {{ $gettext('WebAuthN registration') }} </span>
    </v-card-title>
    <v-card-text>

      <v-btn color="success" :loading="registrationLoading" @click="startFidoRegistration">{{ $gettext('Register device') }}</v-btn>
    </v-card-text>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn color="grey darken-1" text @click="close">
        {{ $gettext('Close') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="js">
import { useGettext } from 'vue3-gettext'
import { ref, onMounted } from 'vue'


const { $gettext } = useGettext()
const name = ref()
const registrationLoading = ref(false)
const publicKey = ref()

async function startFidoRegistration() {
  if (publicKey.value) {
    navigator.credentials.create(publicKey.value)
      .then(function (attestation) {
        // Send new credential info to server for verification and registration.
        console.log(attestation)
      })
      .catch(function (err) {
        // No acceptable authenticator or user refused consent. Handle appropriately.
        console.log(err)
    })
  }
}

onMounted(() => {
  registrationLoading.value = true
  authApi.beginFidoRegistration().then((resp) => {
    publicKey.value = resp.data.publicKey
  }).finally(() => registrationLoading.value = false)
})

const emit = defineEmits(['close'])
function close() {
  emit('close')
}
</script>
