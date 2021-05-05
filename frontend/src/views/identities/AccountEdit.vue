<template>
<div>
  <span class="text-h4"><translate>Edit account</translate></span>
  <div class="mt-4" />
  <account-form :account="account" />
</div>
</template>

<script>
import accounts from '@/api/accounts'
import AccountForm from '@/components/identities/AccountForm'

export default {
  components: {
    AccountForm
  },
  data () {
    return {
      account: {}
    }
  },
  mounted () {
    accounts.get(this.$route.params.id).then(resp => {
      this.account = resp.data
    })
  }
}
</script>
