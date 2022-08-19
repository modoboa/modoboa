<template>
<button @click="copyDNSToClipboard()" class='dkimbutton'><p id='dkimdns' class='dkim'>
{{ domain.dkim_key_selector }}._domain_key.{{ domain.name }}. IN TXT ({{ splitKey(`v=DKIM1;k=rsa;p=${domain.dkim_public_key}`) }})</p></button>
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
    copyDNSToClipboard () {
      const text = document.getElementById('dkimdns').textContent
      navigator.clipboard.writeText(text)
    }
  }
}
</script>
