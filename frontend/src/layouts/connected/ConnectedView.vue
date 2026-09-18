<template>
  <v-main>
    <v-container
      fluid
      class="connected-container"
      :class="{ 'connected-container-with-header': $slots.header }"
    >
      <!-- A title shared by every view of a section. It also keeps them
           clear of the top menu, fixed in the top right corner. -->
      <slot name="header" />
      <div class="connected-content">
        <router-view v-slot="{ Component }">
          <transition name="fade">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
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

.connected-container {
  height: 100%;
}

.connected-content {
  height: 100%;
}

/* The views fill what the header leaves: their h-100 is the height of
   the content area, not of the whole page */
.connected-container-with-header {
  display: flex;
  flex-direction: column;
}

.connected-container-with-header .connected-content {
  flex: 1 1 auto;
  min-height: 0;
  height: auto;
}
</style>
