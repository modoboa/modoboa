<template>
  <v-card>
    <v-card-title>
      <div class="headline">{{ $gettext('General information') }}</div>
    </v-card-title>
    <v-card-text>
      <v-row>
        <v-col cols="6">{{ $gettext('Creation date') }}</v-col>
        <v-col cols="6">{{ $date(alias.creation) }}</v-col>
      </v-row>
      <v-row>
        <v-col cols="6">{{ $gettext('Modified') }}</v-col>
        <v-col cols="6">{{ $date(alias.last_modification) }}</v-col>
      </v-row>
      <v-row v-if="alias.expiry">
        <v-col cols="6">{{ $gettext('Expire at') }}</v-col>
        <v-col cols="6"></v-col>
      </v-row>
      <v-row v-if="alias.description">
        <v-col cols="6">{{ $gettext('Description') }}</v-col>
        <v-col cols="6">{{ alias.description }}</v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup lang="js">
defineProps({ alias: { type: Object, default: null } })
</script>
