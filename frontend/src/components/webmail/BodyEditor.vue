<template>
  <HtmlEditor
    v-if="htmlMode"
    v-model="model"
    class="d-flex flex-column flex-grow-1 mt-4"
  >
    <template #append-toolbar>
      <v-btn-toggle
        v-model="selection"
        base-color="grey-lighten-3"
        color="primary"
        class="mr-2"
      >
        <v-btn text="HTML" size="small" @click="toggleHtmlMode" />
      </v-btn-toggle>
    </template>
  </HtmlEditor>
  <template v-else>
    <div class="mt-8">
      <v-btn-toggle
        v-model="selection"
        base-color="grey-lighten-3"
        color="primary"
        class="mr-2"
      >
        <v-btn v-btn text="HTML" size="small" @click="toggleHtmlMode"> </v-btn>
      </v-btn-toggle>
    </div>
    <v-textarea v-model="model" class="border-sm" />
  </template>
</template>

<script setup>
import { ref, watch } from 'vue'
import HtmlEditor from '@/components/tools/HtmlEditor'

const props = defineProps({
  editorMode: {
    type: String,
    default: null,
  },
})

const model = defineModel()
const emit = defineEmits(['onToggleHtmlMode'])

const htmlMode = ref(false)
const selection = ref()

const toggleHtmlMode = () => {
  htmlMode.value = !htmlMode.value
  emit('onToggleHtmlMode', htmlMode.value)
}

watch(
  () => props.editorMode,
  (value) => {
    htmlMode.value = value === 'html'
  }
)
</script>
