<template>
<button @click="copyDNSToClipboard()" class='dkimbutton'><p id='dkimdns' class='dkim'>
{{ domain.dkim_key_selector }}._domain_key.{{ domain.name }}. IN TXT "v=DKIM1;k=rsa;p={{ domain.dkim_public_key }}"</p></button>
</template>

<script>
export default {
  props: {
    domain: Object
  },
  methods: {
    copyDNSToClipboard () {
      const text = document.getElementById('dkimdns').textContent
      navigator.clipboard.writeText(text)
    }
  }
}
</script>
