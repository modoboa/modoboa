<template>
  <v-card>
    <v-card-title>
      <div class="headline">{{ $gettext('Recipients') }}</div>
    </v-card-title>
    <v-card-text>
      <p v-for="recipient in alias.recipients" :key="recipient">
        {{ recipient }}
      </p>
    </v-card-text>
  </v-card>
</template>

<script setup lang="js">
defineProps({ alias: { type: Object, default: null } })
</script>
