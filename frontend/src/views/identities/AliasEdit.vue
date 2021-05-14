<template>
<div>
  <span class="text-h4"><translate>Edit alias</translate></span>
  <div class="mt-4" />
  <alias-form :alias="alias" />
</div>
</template>

<script>
import aliases from '@/api/aliases'
import AliasForm from '@/components/identities/AliasForm'

export default {
  components: {
    AliasForm
  },
  data () {
    return {
      alias: {}
    }
  },
  mounted () {
    aliases.get(this.$route.params.id).then(resp => {
      this.alias = resp.data
    })
  }
}
</script>
