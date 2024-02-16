<template>
  <v-card>
    <v-card-title>
      <span class="headline">{{ $gettext('Aliases') }}</span>
    </v-card-title>
    <v-card-text>
      <v-chip v-for="alias in account.aliases" :key="alias" class="mr-2 mt-2">
        {{ alias }}
      </v-chip>
    </v-card-text>
  </v-card>
</template>

<script setup lang="js">
defineProps({ account: { type: Object, default: null } })
</script>
