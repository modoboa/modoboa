<template>
<v-card>
  <v-card-title>
    <translate class="headline">General information</translate>
  </v-card-title>
  <v-card-text>
    <v-row>
      <v-col cols="6"><translate>Creation date</translate></v-col>
      <v-col cols="6">{{ alias.creation|date }}</v-col>
    </v-row>
    <v-row>
      <v-col cols="6"><translate>Modified</translate></v-col>
      <v-col cols="6">{{ alias.last_modification|date }}</v-col>
    </v-row>
    <v-row v-if="alias.expiry">
      <v-col cols="6"><translate>Expire at</translate></v-col>
      <v-col cols="6"></v-col>
    </v-row>
    <v-row v-if="alias.description">
      <v-col cols="6"><translate>Description</translate></v-col>
      <v-col cols="6">{{ alias.description }}</v-col>
    </v-row>
  </v-card-text>
</v-card>
</template>

<script>
export default {
  props: {
    alias: Object
  }
}
</script>
