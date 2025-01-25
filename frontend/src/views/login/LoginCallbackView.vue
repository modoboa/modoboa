<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores'

const props = defineProps({
  redirectUrl: String,
})

const authStore = useAuthStore()

onMounted(() => {
  authStore.completeLogin(props.redirectUrl)
})
</script>

<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="auto" class="text-center">
      <h1 class="ma-5">{{ $gettext('Attempting to log you in.') }}</h1>
      <v-progress-circular
        color="primary"
        indeterminate
        :size="128"
        :width="12"
        align-self="center"
      ></v-progress-circular>
      </v-col>
    </v-row>
  </v-container>
</template>
