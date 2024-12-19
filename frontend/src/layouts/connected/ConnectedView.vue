<template>
  <v-main>
    <v-container fluid>
      <router-view v-slot="{ Component }">
        <transition name="fade">
          <div v-show="true">
            <component :is="Component" />
          </div>
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
