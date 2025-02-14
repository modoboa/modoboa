<template>
  <v-btn icon flat color="primary">
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
        </v-list>
      </v-card>
    </v-menu>
  </v-btn>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  user: {
    type: Object,
    default: null,
  },
})

const userInitials = computed(() => {
  if (!props.user) {
    return ''
  }
  return props.user.first_name && props.user.last_name
    ? `${props.user.first_name[0].toUpperCase()}${props.user.last_name[0].toUpperCase()}`
    : props.user.username.slice(0, 2).toUpperCase()
})
</script>
