<template>
<v-card>
  <v-card-title>
    <translate class="headline">Recipients</translate>
  </v-card-title>
  <v-card-text>
    <p v-for="recipient in alias.recipients" :key="recipient">{{ recipient }}</p>
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
