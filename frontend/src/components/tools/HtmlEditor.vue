<template>
  <div>
    <div ref="toolbar" class="mt-4">
      <slot name="append-toolbar"></slot>
      <v-btn-toggle
        v-if="editor"
        v-model="selection"
        base-color="grey-lighten-3"
        color="primary"
        multiple
      >
        <v-btn
          icon="mdi-format-bold"
          :class="{ 'is-active': editor.isActive('bold') }"
          size="small"
          value="bold"
          @click="editor.chain().focus().toggleBold().run()"
        />
        <v-btn
          icon="mdi-format-italic"
          :class="{ 'is-active': editor.isActive('italic') }"
          size="small"
          value="italic"
          @click="editor.chain().focus().toggleItalic().run()"
        />
        <v-btn
          icon="mdi-format-strikethrough"
          :class="{ 'is-active': editor.isActive('strike') }"
          size="small"
          value="strike"
          @click="editor.chain().focus().toggleStrike().run()"
        />
        <v-divider vertical />
        <v-btn
          icon="mdi-format-align-left"
          :class="{ 'is-active': editor.isActive({ textAlign: 'left' }) }"
          size="small"
          value="left"
          @click="editor.chain().focus().setTextAlign('left').run()"
        />
        <v-btn
          icon="mdi-format-align-center"
          :class="{ 'is-active': editor.isActive({ textAlign: 'center' }) }"
          size="small"
          value="center"
          @click="editor.chain().focus().setTextAlign('center').run()"
        />
        <v-btn
          icon="mdi-format-align-right"
          :class="{ 'is-active': editor.isActive({ textAlign: 'right' }) }"
          size="small"
          value="right"
          @click="editor.chain().focus().setTextAlign('right').run()"
        />
        <v-btn
          icon="mdi-format-align-justify"
          :class="{ 'is-active': editor.isActive({ textAlign: 'justify' }) }"
          size="small"
          value="justify"
          @click="editor.chain().focus().setTextAlign('justify').run()"
        />
        <v-divider vertical />
        <v-btn
          icon="mdi-format-list-bulleted"
          :class="{ 'is-active': editor.isActive('bulletList') }"
          size="small"
          value="bullet"
          @click="editor.chain().focus().toggleBulletList().run()"
        />
        <v-btn
          icon="mdi-format-list-numbered"
          :class="{ 'is-active': editor.isActive('orderedList') }"
          size="small"
          value="ordered"
          @click="editor.chain().focus().toggleOrderedList().run()"
        />
      </v-btn-toggle>
      <v-btn-group v-if="editor" class="ml-2" color="grey-lighten-3">
        <v-btn
          icon="mdi-undo"
          :disabled="!editor.can().chain().focus().undo().run()"
          size="small"
          value="undo"
          @click="editor.chain().focus().undo().run()"
        />
        <v-btn
          icon="mdi-redo"
          :disabled="!editor.can().chain().focus().redo().run()"
          size="small"
          value="redo"
          @click="editor.chain().focus().redo().run()"
        />
      </v-btn-group>
    </div>
    <EditorContent
      :editor="editor"
      class="border-sm d-flex flex-column flex-grow-1 pa-4"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import Highlight from '@tiptap/extension-highlight'
import TextAlign from '@tiptap/extension-text-align'
import StarterKit from '@tiptap/starter-kit'
import { useEditor, EditorContent } from '@tiptap/vue-3'

const props = defineProps({
  modelValue: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['update:modelValue'])

const selection = ref([])
const toolbar = ref()

const editor = useEditor({
  content: props.modelValue,
  extensions: [
    StarterKit,
    TextAlign.configure({
      types: ['heading', 'paragraph'],
    }),
    Highlight,
  ],
  onUpdate: () => {
    emit('update:modelValue', editor.value.getHTML())
  },
})

watch(
  () => props.modelValue,
  (value) => {
    if (editor.value.getHTML() === value) {
      return
    }
    editor.value.commands.setContent(value, false)
  }
)
</script>

<style lang="scss">
.tiptap {
  flex-grow: 1;
  :first-child {
    margin-top: 0;
  }
  ul,
  ol {
    padding: 0 1rem;
    margin: 1.25rem 1rem 1.25rem 0.4rem;
    li p {
      margin-top: 0.25em;
      margin-bottom: 0.25em;
    }
  }
}
</style>
