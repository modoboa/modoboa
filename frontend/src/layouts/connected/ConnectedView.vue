<template>
  <v-main>
    <v-container fluid style="height: 100%">
      <router-view v-slot="{ Component }">
        <transition name="fade">
          <component :is="Component" />
        </transition>
      </router-view>
    </v-container>
  </v-main>
</template>

<script setup>
//
</script>

<style scoped>
.v-main {
  background-color: #f7f8fa;
}
</style>
