<template>
<v-card>
  <v-card-title>
    <translate class="headline">Aliases</translate>
  </v-card-title>
  <v-card-text>
    <v-chip v-for="alias in account.aliases" :key="alias" class="mr-2 mt-2">
      {{ alias }}
    </v-chip>
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
