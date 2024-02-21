<template>
  <v-card>
    <v-card-title>
      <span class="headline">{{ $gettext('Administered domains') }}</span>
    </v-card-title>
    <v-card-text>
      <template v-if="account.domains !== undefined && account.domains.length">
        <v-row v-for="domain in account.domains" :key="domain">
          <v-col cols="12">{{ domain }}</v-col>
        </v-row>
      </template>
      <div v-else>
        {{ $gettext('No domain managed') }}
      </div>
      <div class="text-disabled">
        {{ $gettext('Add/Remove from the domain page') }}
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="js">
import { useGettext } from 'vue3-gettext'

const { $gettext } = useGettext()
defineProps({ account: { type: Object, default: null } })
</script>
