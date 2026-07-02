<template>
  <div ref="root" class="swipeable-row">
    <!-- Action backgrounds revealed as the content slides. Left swipe (content
         moves left) reveals the right-aligned delete action; right swipe
         reveals the left-aligned read-toggle action. -->
    <div
      v-if="leftAction"
      class="swipeable-row__action swipeable-row__action--left"
      :class="{
        'swipeable-row__action--armed': armed === 'left',
        'swipeable-row__action--visible': swiping || armed,
      }"
      :style="{ backgroundColor: `rgb(var(--v-theme-${leftAction.color}))` }"
    >
      <v-icon :icon="leftAction.icon" />
      <span>{{ leftAction.label }}</span>
    </div>
    <div
      v-if="rightAction"
      class="swipeable-row__action swipeable-row__action--right"
      :class="{
        'swipeable-row__action--armed': armed === 'right',
        'swipeable-row__action--visible': swiping || armed,
      }"
      :style="{ backgroundColor: `rgb(var(--v-theme-${rightAction.color}))` }"
    >
      <v-icon :icon="rightAction.icon" />
      <span>{{ rightAction.label }}</span>
    </div>

    <div
      class="swipeable-row__content"
      :class="{ 'swipeable-row__content--swiping': swiping }"
      :style="{ transform: `translateX(${offsetX}px)` }"
    >
      <slot />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useHorizontalSwipe } from '@/composables/useHorizontalSwipe'

const props = defineProps({
  enabled: { type: Boolean, default: true },
  // { icon, color, label } — color is a Vuetify theme key (error/primary/...)
  leftAction: { type: Object, default: null },
  rightAction: { type: Object, default: null },
})

const emit = defineEmits(['swipe-left', 'swipe-right'])

const root = ref(null)

const { offsetX, swiping, armed } = useHorizontalSwipe(root, {
  enabled: () => props.enabled,
  onTrigger: (direction) => {
    emit(direction === 'left' ? 'swipe-left' : 'swipe-right')
  },
})
</script>

<style scoped>
.swipeable-row {
  position: relative;
  overflow: hidden;
  /* Browser owns vertical panning; horizontal reaches our pointer handlers. */
  touch-action: pan-y;
}
.swipeable-row__action {
  position: absolute;
  top: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 20px;
  color: #fff;
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  opacity: 0;
  transition: opacity 0.1s;
}
.swipeable-row__action--visible {
  opacity: 0.85;
}
.swipeable-row__action--armed {
  opacity: 1;
}
.swipeable-row__action--left {
  right: 0;
  justify-content: flex-end;
}
.swipeable-row__action--right {
  left: 0;
  justify-content: flex-start;
}
.swipeable-row__content {
  position: relative;
  background: var(--bg);
  will-change: transform;
}
/* Snap back / settle when the finger is up; follow 1:1 while swiping. */
.swipeable-row__content:not(.swipeable-row__content--swiping) {
  transition: transform 0.15s ease;
}
</style>
