<template>
  <v-radio-group v-model="model" inline>
    <v-radio :label="$gettext('yes')" value="Y" />
    <v-radio :label="$gettext('no')" value="N" />
    <v-radio :label="$gettext('default')" value="" />
  </v-radio-group>
</template>

<script setup>
const model = defineModel()
</script>
