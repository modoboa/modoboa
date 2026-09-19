<template>
  <!--
    The message body is untrusted: render it in a sandboxed iframe so it
    can never reach the application context, even if the server-side HTML
    cleaner is bypassed. Scripts stay forbidden, by the sandbox and by the
    CSP below: 'allow-same-origin' is only there so that the parent can
    measure the content and size the frame, which an opaque origin
    forbids. It is safe *because* 'allow-scripts' is not granted: without
    it the document cannot execute anything, so it cannot use that origin.
  -->
  <iframe
    ref="frame"
    class="email-body"
    sandbox="allow-popups allow-popups-to-escape-sandbox allow-same-origin"
    referrerpolicy="no-referrer"
    :srcdoc="document"
    :style="{ height: `${height}px` }"
    @load="onLoad"
  />
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  body: {
    type: String,
    default: '',
  },
  enableImages: {
    type: Boolean,
    default: false,
  },
})

// Used until the content has been measured, and if it can't be
const DEFAULT_HEIGHT = 300

const frame = ref(null)
const height = ref(DEFAULT_HEIGHT)
let observer = null

const document = computed(() => {
  if (!props.body) {
    return ''
  }
  // Remote content (images, fonts, etc.) is only allowed once the reader
  // asks for the images, which keeps tracking pixels from loading by
  // default, whatever the links are set to.
  const remoteSrc = props.enableImages ? ' https: http:' : ''
  const csp = [
    "default-src 'none'",
    `img-src data:${remoteSrc}`,
    `media-src data:${remoteSrc}`,
    `font-src data:${remoteSrc}`,
    "style-src 'unsafe-inline'",
    "form-action 'none'",
  ].join('; ')
  return `
    <!DOCTYPE html><html><head><meta charset="utf-8">
    <meta http-equiv="Content-Security-Policy" content="${csp}">
    <base target="_blank">
    <style>body { margin: 0; font-family: sans-serif; }</style>
    </head><body>
    ${props.body}
    </body></html>
  `
})

const measure = () => {
  try {
    const doc = frame.value?.contentDocument
    if (!doc?.body) {
      return
    }
    height.value = Math.max(
      doc.documentElement.scrollHeight,
      doc.body.scrollHeight,
      DEFAULT_HEIGHT
    )
  } catch {
    // The content couldn't be measured: keep the current height
  }
}

const stopObserving = () => {
  observer?.disconnect()
  observer = null
}

const onLoad = () => {
  stopObserving()
  measure()
  // Images and fonts arriving later change the height
  try {
    const doc = frame.value?.contentDocument
    if (doc?.body && window.ResizeObserver) {
      observer = new ResizeObserver(measure)
      observer.observe(doc.body)
    }
  } catch {
    // Without an observer the height stays the one measured on load
  }
}

watch(() => props.body, stopObserving)

onBeforeUnmount(stopObserving)
</script>

<style scoped>
.email-body {
  display: block;
  width: 100%;
  overflow: hidden;
  border: none;
  background-color: #fff;
}
</style>
