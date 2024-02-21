<template>
  <v-text-field
    ref="inputRef"
    v-model="input"
    variant="outlined"
    v-bind="$attrs"
    :error-messages="errors"
    :error="errors.length > 0"
    density="compact"
    autocomplete="new-password"
    @keydown="onKeyDown"
  />
  <div v-if="showMenu" class="menu" :style="`width: ${width}px;`">
    <v-list class="list">
      <v-list-item
        v-for="(domain, index) in filteredDomains"
        :key="index"
        :class="selectionIndex === index ? 'bg-primary-lighten-1' : ''"
        @click="selectDomain(domain)"
        @mouseenter="selectionIndex = index"
      >
        <v-list-item-title>{{ domain.name }}</v-list-item-title>
      </v-list-item>
    </v-list>
  </div>
</template>

<script setup lang="js">
import { ref, computed, onMounted, onUnmounted, onUpdated, nextTick } from 'vue'
import { useDomainsStore } from '@/stores'
import { useGettext } from 'vue3-gettext'

const { $gettext } = useGettext()
const domainsStore = useDomainsStore()
const props = defineProps({
  modelValue: { type: String, default: '' },
  allowAdd: { type: Boolean, default: false },
  role: { type: String, default: 'SimpleUsers' },
  errorMsg: { type: Array, default: () => [] },
})
const emit = defineEmits(['domain-selected', 'update:model-value'])

const input = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    errors.value = []
    if (value.indexOf('@') !== -1) {
      if (props.role !== 'SuperAdmins') {
        domainSearch.value = value.split('@')[1]
        if (props.allowAdd) {
          showMenu.value = filteredDomains.value.length > 0
        } else {
          showMenu.value = true
        }
      } else {
        errors.value = [$gettext('SuperAdmins cannot own a mailbox')]
      }
    } else {
      showMenu.value = false
    }
    emit('update:model-value', value)
  },
})

const filteredDomains = computed(() => {
  return Object.values(domainsStore.domains).filter((domain) =>
    domain.name.startsWith(domainSearch.value)
  )
})

const errors = computed({
  get() {
    return [...localErrors.value, ...props.errorMsg]
  },
  set(value) {
    localErrors.value = value
  },
})

const domainSearch = ref('')
const selectionIndex = ref(0)
const showMenu = ref(false)
const width = ref(500)
const inputRef = ref()
const localErrors = ref([])

function onKeyDown(e) {
  if (props.role === 'SuperAdmins') {
    // No mailbox for SuperAdmins
    return
  }
  const keyCode = e.keyCode
  if (keyCode === 40 || keyCode === 34) {
    // on arrow down or page down
    if (!showMenu.value) {
      domainSearch.value = ''
      showMenu.value = true
    } else {
      increaseSelectionIndex()
    }
    e.preventDefault()
  } else if (keyCode === 38 || keyCode === 33) {
    // on arrow up or page up
    if (!showMenu.value) {
      domainSearch.value = ''
      showMenu.value = true
    } else {
      decreaseSelectionIndex()
    }
    e.preventDefault()
  } else if (keyCode === 13 || keyCode === 9) {
    // on enter or tab
    if (filteredDomains.value.length > 0) {
      selectDomain(filteredDomains.value[selectionIndex.value])
    } else if (props.allowAdd) {
      selectDomain()
    }
    e.preventDefault()
  } else if (keyCode === 27) {
    // on escape
    if (filteredDomains.value.length > 0) {
      showMenu.value = false
      e.preventDefault()
    }
  }
}

function increaseSelectionIndex() {
  if (selectionIndex.value >= filteredDomains.value.length - 1) {
    selectionIndex.value = 0
  } else {
    selectionIndex.value += 1
  }
}

function decreaseSelectionIndex() {
  if (selectionIndex.value <= 0) {
    selectionIndex.value = filteredDomains.value.length - 1
  } else {
    selectionIndex.value -= 1
  }
}

function selectDomain(domain) {
  if (domain !== undefined) {
    input.value = input.value.split('@')[0] + '@' + domain.name
  }
  showMenu.value = false
  emit('domain-selected')
}

function updateMinWidthProperty() {
  width.value = inputRef.value.$el.clientWidth
}

onMounted(() => {
  domainsStore.getDomains()
  window.addEventListener('resize', updateMinWidthProperty)
})
onUnmounted(() => {
  window.removeEventListener('resize', updateMinWidthProperty)
})
onUpdated(() => {
  nextTick(() => {
    updateMinWidthProperty()
  })
})
</script>

<style scoped>
.menu {
  display: inline-block;
  position: fixed;
  margin-top: -20px;
  padding: 5px 0;
  box-shadow: 0 1px 5px 1px rgba(0, 0, 0, 0.3);
  overflow-y: auto;
  overflow-x: hidden;
  contain: content;
  z-index: 99;
}

.list {
  width: 100%;
  height: 100%;
  font-size: 1.1em;
  overflow-x: hidden;
  padding: 0;
}
</style>
