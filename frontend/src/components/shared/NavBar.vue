<template>
  <v-navigation-drawer
    v-model="drawer"
    :rail="rail"
    permanent
    :color="color"
    app
  >
    <div class="d-flex align-center">
      <v-img
        src="@/assets/Modoboa_RVB-BLANC-SANS.png"
        max-width="190"
        class="logo"
        @click="router.push(props.logoRoute)"
      />
      <v-btn
        :icon="rail ? 'mdi-chevron-right' : 'mdi-chevron-left'"
        variant="text"
        @click.stop="rail = !rail"
      >
      </v-btn>
    </div>

    <v-list nav>
      <template v-for="item in menuItems" :key="item.text">
        <template v-if="displayMenuItem(item)">
          <v-list-subheader v-if="item.subheader" class="text-white">
            {{ item.text.toUpperCase() }}
          </v-list-subheader>
          <v-list-item
            v-else-if="item.action"
            :value="item"
            :exact="item.exact"
            :title="item.text"
            :prepend-icon="item.icon"
            @click="item.action"
          >
          </v-list-item>
          <v-list-item
            v-else-if="!item.children"
            :value="item"
            :to="item.to"
            link
            :exact="item.exact"
            :title="item.text"
            :prepend-icon="item.icon"
          >
            <template v-if="item.withBell && displayInformationBell" #append>
              <v-icon color="red" icon="mdi-bell-alert-outline" />
            </template>
          </v-list-item>
          <v-list-group v-else :value="item.text">
            <template #activator="{ props }">
              <v-list-item
                v-bind="props"
                :key="item.text"
                :title="item.text"
                color="white"
                :prepend-icon="item.icon"
              >
              </v-list-item>
            </template>
            <template v-for="subitem in item.children" :key="subitem.text">
              <template v-if="displayMenuItem(subitem)">
                <v-list-item
                  v-if="subitem.action"
                  :title="subitem.text"
                  :value="subitem"
                  :prepend-icon="subitem.icon"
                  @click="subitem.action"
                ></v-list-item>
                <v-list-item
                  v-else
                  :to="subitem.to"
                  link
                  :title="subitem.text"
                  :value="subitem"
                  :prepend-icon="subitem.icon"
                ></v-list-item>
              </template>
            </template>
          </v-list-group>
        </template>
      </template>
    </v-list>
  </v-navigation-drawer>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ref, computed, onMounted } from 'vue'
import { useGlobalStore, useAuthStore } from '@/stores'

const props = defineProps({
  color: {
    type: String,
    default: 'primary',
  },
  menuItems: {
    type: Array,
    required: false,
    default: null,
  },
  logoRoute: {
    type: Object,
    default: null,
  },
})

const globalStore = useGlobalStore()
const authStore = useAuthStore()
const router = useRouter()

const rail = ref(false)
const drawer = ref(true)

const authUser = computed(() => authStore.authUser)
const isAuthenticated = computed(() => authStore.isAuthenticated)

const displayInformationBell = computed(
  () =>
    globalStore.notifications.length !== undefined &&
    globalStore.notifications.length !== 0
)

function displayMenuItem(item) {
  if (isAuthenticated.value) {
    const condition =
      (item.roles === undefined ||
        item.roles.indexOf(authUser.value.role) !== -1) &&
      (item.condition === undefined || item.condition()) &&
      item.activated !== false
    return condition
  }
  return false
}

onMounted(() => {
  if (authUser.value.role === 'SuperAdmins') {
    globalStore.fetchNotifications()
  }
})
</script>

<style lang="scss" scoped>
.v-list-item {
  &--active {
    &::before {
      opacity: 0;
    }
    background-color: #034bad !important;
    color: white;
    opacity: 1;
  }
}

.v-list-subheader {
  &__text {
    color: white !important;
  }
}

.logo {
  cursor: pointer;
}
</style>
