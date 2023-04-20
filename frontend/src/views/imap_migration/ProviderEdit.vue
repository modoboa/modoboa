<template>
<div>
  <span class="text-h4"><translate>Edit provider</translate></span>
  <div class="mt-4" />
  <provider-form :provider="provider" />
</div>
</template>

<script>
import providers from '@/api/imap_migration/providers'
import ProviderForm from '@/components/imap_migration/ProviderForm'

export default {
  components: {
    ProviderForm
  },
  data () {
    return {
      provider: {}
    }
  },
  mounted () {
    providers.getProvider(this.$route.params.id).then(resp => {
      this.provider = resp.data
    })
  }
}
</script>
