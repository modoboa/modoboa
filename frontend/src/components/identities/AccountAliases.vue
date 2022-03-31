<template>
<v-card>
  <v-card-title>
    <translate class="headline">Aliases</translate>
  </v-card-title>
  <v-card-text>
    <p v-for="alias in account.aliases" :key="alias">
      {{ alias }}
    </p>
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
