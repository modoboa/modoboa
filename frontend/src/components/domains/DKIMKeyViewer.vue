<template>
  <button @click="copyDKIM()" class="dkimbutton">
    <pre id="dkimdns" class="dkim">{{ domain.dkim_key_selector }}._domainkey.{{ domain.name }}. IN TXT ({{ splitKey(`v=DKIM1;k=rsa;p=${domain.dkim_public_key}`) }})</pre>
  </button>
</template>

<script>
export default {
  props: {
    domain: Object
  },
  methods: {
    splitKey (value) {
      let key = value
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
    },
    copyDKIM () {
      navigator.clipboard.writeText(document.getElementById('dkimdns').textContent)
    }
  }
}
</script>
