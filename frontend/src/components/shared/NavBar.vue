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
        :src="menuLogoPath"
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

    <v-list
      :density="layoutStore.compactLeftMenu ? 'compact' : 'default'"
      :lines="layoutStore.compactLeftMenu ? false : true"
      nav
    >
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
import { ref, computed } from 'vue'
import { useLogos } from '@/composables/logos'
import { useAuthStore, useLayoutStore } from '@/stores'

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

const authStore = useAuthStore()
const layoutStore = useLayoutStore()
const router = useRouter()
const { menuLogoPath } = useLogos()

const rail = ref(false)
const drawer = ref(true)

const authUser = computed(() => authStore.authUser)
const isAuthenticated = computed(() => authStore.isAuthenticated)

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
</script>

<style lang="scss" scoped>
.logo {
  cursor: pointer;
}
</style>
