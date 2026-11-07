<template>
  <template v-if="compact">
    <!-- Short colored marks, named on hover: the listing has little room -->
    <span
      v-for="tag in known"
      :key="tag.keyword"
      class="tag-mark"
      :style="{ backgroundColor: tag.color }"
      :title="tag.label"
      role="img"
      :aria-label="tag.label"
    />
  </template>
  <template v-else>
    <v-chip
      v-for="tag in known"
      :key="tag.keyword"
      :color="tag.color"
      class="me-1"
      size="x-small"
      variant="flat"
      label
    >
      {{ tag.label }}
    </v-chip>
  </template>
</template>

<script setup>
import { computed } from 'vue'
import { useWebmailStore } from '@/stores'

const props = defineProps({
  keywords: {
    type: Array,
    default: () => [],
  },
  compact: {
    type: Boolean,
    default: false,
  },
})

const webmailStore = useWebmailStore()

// Keywords set by other clients, or by a deleted tag, aren't displayed
const known = computed(() =>
  props.keywords
    .map((keyword) => webmailStore.tagsByKeyword[keyword])
    .filter(Boolean)
)
</script>

<style scoped>
.tag-mark {
  display: inline-block;
  width: 14px;
  height: 8px;
  margin-right: 3px;
  border-radius: 4px;
  vertical-align: middle;
}

.tag-mark:last-of-type {
  margin-right: 6px;
}
</style>
