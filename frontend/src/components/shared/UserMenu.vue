<template>
  <v-fab app icon flat location="top right" color="primary">
    {{ userInitials }}
    <v-menu activator="parent" location="bottom">
      <v-card min-width="300" max-width="350">
        <v-list>
          <div class="text-center">
            <v-avatar color="primary">
              <span class="text-h5">{{ userInitials }}</span>
            </v-avatar>
            <v-list-item :title="user.username" />
          </div>
          <v-divider></v-divider>
          <template v-if="remote">
            <v-list-item href="https://localhost:3000/account">
              <template #prepend>
                <v-icon icon="mdi-account-circle-outline"></v-icon>
              </template>
              <v-list-item-title>Account</v-list-item-title>
            </v-list-item>
            <v-list-item @click="logout">
              <template #prepend>
                <v-icon icon="mdi-logout"></v-icon>
              </template>
              <v-list-item-title>Logout</v-list-item-title>
            </v-list-item>
          </template>
        </v-list>
      </v-card>
    </v-menu>
  </v-fab>
</template>

<script setup>
import { computed } from 'vue'
import { getActivePinia } from 'pinia'

const props = defineProps({
  user: {
    type: Object,
    default: null,
  },
  remote: {
    type: Boolean,
    default: false,
  },
})

const userInitials = computed(() => {
  return props.user.first_name && props.user.last_name
    ? `${props.user.first_name[0].toUpperCase()}${props.user.last_name[0].toUpperCase()}`
    : props.user.username.slice(0, 2).toUpperCase()
})

async function logout() {
  getActivePinia()._s.forEach(async (store) => await store.$reset())
}
</script>
