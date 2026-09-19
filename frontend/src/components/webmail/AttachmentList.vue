<template>
  <div v-if="attachments.length" class="mail-attachments">
    <div class="mail-attachments-title">
      <v-icon icon="mdi-paperclip" size="small" />
      {{ title }}
    </div>
    <div class="mail-attachments-items">
      <v-btn
        v-for="attachment in attachments"
        :key="attachment.partnum"
        class="mail-attachment"
        variant="text"
        height="auto"
        rounded="lg"
        border
        :title="$gettext('Download %{name}', { name: attachment.name })"
        @click="$emit('download', attachment)"
      >
        <template #prepend>
          <v-icon
            :icon="icon(attachment)"
            size="large"
            class="mail-attachment-icon"
          />
        </template>
        <span class="mail-attachment-text">
          <span class="mail-attachment-name">{{ attachment.name }}</span>
          <span class="mail-attachment-meta">{{ meta(attachment) }}</span>
        </span>
        <template #append>
          <v-icon
            icon="mdi-download"
            size="small"
            class="mail-attachment-action"
          />
        </template>
      </v-btn>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useGettext } from 'vue3-gettext'

const props = defineProps({
  attachments: {
    type: Array,
    default: () => [],
  },
})

defineEmits(['download'])

const { $gettext, $ngettext } = useGettext()

// Icons for the kinds of file a message actually carries, by content
// type first and by extension when the server didn't give one
const ICONS_BY_TYPE = [
  [/^image\//, 'mdi-file-image-outline'],
  [/^audio\//, 'mdi-file-music-outline'],
  [/^video\//, 'mdi-file-video-outline'],
  [/^text\/csv/, 'mdi-file-delimited-outline'],
  [/^text\//, 'mdi-file-document-outline'],
  [/pdf/, 'mdi-file-pdf-box'],
  [/(zip|tar|gzip|compressed|7z|rar)/, 'mdi-folder-zip-outline'],
  [/(word|opendocument\.text)/, 'mdi-file-word-outline'],
  [/(excel|sheet)/, 'mdi-file-excel-outline'],
  [/(powerpoint|presentation)/, 'mdi-file-powerpoint-outline'],
  [/^message\//, 'mdi-email-outline'],
]

const ICONS_BY_EXTENSION = {
  pdf: 'mdi-file-pdf-box',
  png: 'mdi-file-image-outline',
  jpg: 'mdi-file-image-outline',
  jpeg: 'mdi-file-image-outline',
  gif: 'mdi-file-image-outline',
  webp: 'mdi-file-image-outline',
  svg: 'mdi-file-image-outline',
  zip: 'mdi-folder-zip-outline',
  gz: 'mdi-folder-zip-outline',
  tar: 'mdi-folder-zip-outline',
  doc: 'mdi-file-word-outline',
  docx: 'mdi-file-word-outline',
  odt: 'mdi-file-word-outline',
  xls: 'mdi-file-excel-outline',
  xlsx: 'mdi-file-excel-outline',
  ods: 'mdi-file-excel-outline',
  csv: 'mdi-file-delimited-outline',
  ppt: 'mdi-file-powerpoint-outline',
  pptx: 'mdi-file-powerpoint-outline',
  txt: 'mdi-file-document-outline',
  eml: 'mdi-email-outline',
}

const icon = (attachment) => {
  const type = (attachment.content_type || '').toLowerCase()
  for (const [pattern, name] of ICONS_BY_TYPE) {
    if (pattern.test(type)) {
      return name
    }
  }
  const extension = attachment.name?.split('.').pop()?.toLowerCase()
  return ICONS_BY_EXTENSION[extension] || 'mdi-file-outline'
}

// The size announced by the body structure is the encoded one, so it
// is shown as an approximation rather than an exact figure
const meta = (attachment) => {
  const parts = []
  if (attachment.size) {
    parts.push(`~ ${formatSize(attachment.size)}`)
  }
  const extension = attachment.name?.split('.').pop()?.toLowerCase()
  if (extension && extension !== attachment.name?.toLowerCase()) {
    parts.push(extension.toUpperCase())
  }
  return parts.join(' · ')
}

const formatSize = (size) => {
  const units = ['B', 'KB', 'MB', 'GB']
  let value = size
  let unit = 0
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024
    unit += 1
  }
  return `${value < 10 && unit > 0 ? value.toFixed(1) : Math.round(value)} ${units[unit]}`
}

const title = computed(() => {
  const count = props.attachments.length
  return $ngettext('%{count} attachment', '%{count} attachments', count, {
    count,
  })
})
</script>
