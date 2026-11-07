<template>
  <v-btn
    icon
    variant="text"
    size="small"
    :title="title"
    :disabled="disabled"
    :color="active.length ? 'primary' : undefined"
  >
    <v-icon :icon="active.length ? 'mdi-tag' : 'mdi-tag-outline'" />
    <v-menu activator="parent">
      <v-list density="compact">
        <v-list-item
          v-for="tag in webmailStore.tags || []"
          :key="tag.pk"
          :title="tag.label"
          @click="emit('toggle', tag.keyword, !active.includes(tag.keyword))"
        >
          <template #prepend>
            <v-icon icon="mdi-tag" :color="tag.color" />
          </template>
          <template #append>
            <v-icon v-if="active.includes(tag.keyword)" icon="mdi-check" />
          </template>
        </v-list-item>
        <v-divider />
        <v-list-item
          prepend-icon="mdi-cog-outline"
          :title="$gettext('Manage tags')"
          @click="showForm = true"
        />
      </v-list>
    </v-menu>
  </v-btn>
  <v-dialog v-model="showForm" max-width="500">
    <TagsForm @close="showForm = false" />
  </v-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { useWebmailStore } from '@/stores'
import TagsForm from './TagsForm.vue'

defineProps({
  // Keywords displayed as checked
  active: {
    type: Array,
    default: () => [],
  },
  title: {
    type: String,
    required: true,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

// (keyword, checked): what the click asks for
const emit = defineEmits(['toggle'])

const webmailStore = useWebmailStore()
const showForm = ref(false)
</script>
