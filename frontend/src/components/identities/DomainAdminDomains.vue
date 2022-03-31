<template>
<v-card>
  <v-card-title>
    <translate class="headline">Administered domains</translate>
  </v-card-title>
  <v-card-text>
    <v-row v-for="domain in account.domains" :key="domain">
      <v-col cols="12">{{ domain }}</v-col>
    </v-row>
  </v-card-text>
</v-card>
</template>

<script>
export default {
  props: {
    account: Object
  }
}
</script>
