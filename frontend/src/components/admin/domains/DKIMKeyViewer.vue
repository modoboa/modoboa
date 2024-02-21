<template>
  <button class="dkimbutton" @click="copyDKIM()">
    <pre id="dkimdns" class="dkim"
      >{{ domain.dkim_key_selector }}._domainkey.{{ domain.name }}. IN TXT ({{
        splitKey
      }})
      }})</pre
    >
  </button>
</template>

<script setup lang="js">
import { computed } from 'vue'

const props = defineProps({
  domain: { type: Object, default: null },
})

const splitKey = computed(() => {
  let key = `v=DKIM1;k=rsa;p=${props.domain.dkim_public_key}`
  const result = []
  while (key.length > 0) {
    if (key.length > 74) {
      result.push(`  "${key.substring(0, 74)}"`)
      key = key.substring(74)
    } else {
      result.push(`  "${key}"`)
      break
    }
  }
  return result.join('\n')
})

function copyDKIM() {
  navigator.clipboard.writeText(document.getElementById('dkimdns').textContent)
}
</script>
