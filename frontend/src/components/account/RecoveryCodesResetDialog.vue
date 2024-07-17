<template>
  <v-card>
    <v-card-title>
      <span class="headline"> {{ $gettext('New recovery codes') }} </span>
    </v-card-title>
    <v-card-text>
      <v-alert type="info">
        {{
          $gettext(
            "The following recovery codes can be used one time each to let you regain access to your account, in case you lose your phone for example. Make sure to save them in a safe place, otherwise you won't be able to access your account anymore."
          )
        }}
      </v-alert>
      <v-table class="mt-4" density="compact">
        <tbody>
          <tr v-for="token in tokens" :key="token">
            <td>{{ token }}</td>
          </tr>
        </tbody>
      </v-table>
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

const { $gettext } = useGettext()
defineProps({ tokens: { type: Array, default: null } })
const emit = defineEmits(['close'])
function close() {
  emit('close')
}
</script>
