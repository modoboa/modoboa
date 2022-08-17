<template>
<button @click="copyToClipboard()"><pre>
{{ domain.dkim_key_selector }}._domain_key.{{ domain.name }}. IN TXT (
  {{ splitKey(`v=DKIM1;k=rsa;p=${domain.dkim_public_key}`) }})</pre></button>
</template>

<script>
export default {
  props: {
    domain: Object
  },
  methods: {
    copyToClipboard () {
      const text = domain.dkim_key_selector + '_domain_key.' + domain.name + ' . IN TXT ' + '"v=DKIM1;k=rsa;p=' + domain.dkim_public_key + '"'
      navigator.clipboard.writeText(text)
    },
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
    }
  }
}
</script>
