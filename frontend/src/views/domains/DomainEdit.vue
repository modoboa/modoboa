<template>
<div>
  <span class="text-h4"><translate>Edit domain</translate></span>
  <div class="mt-4" />
  <domain-form :domain="domain" />
</div>
</template>

<script>
import domains from '@/api/domains'
import DomainForm from '@/components/domains/DomainForm'

export default {
  components: {
    DomainForm
  },
  data () {
    return {
      domain: {}
    }
  },
  mounted () {
    domains.getDomain(this.$route.params.id).then(resp => {
      this.domain = resp.data
    })
  }
}
</script>
