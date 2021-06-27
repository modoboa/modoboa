<template>
<v-list dense>
  <v-list-item v-for="(item, index) in items"
               :key="index"
               @click="item.onClick(object)"
               >
    <v-list-item-icon>
      <v-icon :color="item.color">{{ item.icon }}</v-icon>
    </v-list-item-icon>
    <v-list-item-content>
      <v-list-item-title>{{ item.label }}</v-list-item-title>
    </v-list-item-content>
  </v-list-item>
</v-list>
</template>

<script>
export default {
  props: ['items', 'object']
}
</script>
