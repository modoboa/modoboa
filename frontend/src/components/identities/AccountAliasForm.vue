<template>
<validation-observer ref="observer">
  <validation-provider
    vid="alias"
    v-slot="{ errors }"
    >
    <email-field
      ref="aliasField"
      v-model="currentAlias"
      :placeholder="'Start typing a name here...'|translate"
      @domain-selected="addAlias"
      :hint="'Alias(es) of this mailbox. To create a catchall alias, just enter the domain name (@domain.tld).'|translate"
      persistent-hint
      :error-messages="errors"
      />
  </validation-provider>
  <v-chip
    v-for="(alias, index) in account.aliases"
    :key="index"
    class="mr-2 mt-2"
    close
    @click:close="account.aliases.splice(index, 1)"
    >
    {{ alias }}
  </v-chip>
</validation-observer>
</template>

<script>
import accounts from '@/api/accounts'
import EmailField from '@/components/tools/EmailField'

export default {
  props: ['account'],
  components: {
    EmailField
  },
  data () {
    return {
      currentAlias: ''
    }
  },
  methods: {
    async addAlias () {
      try {
        await accounts.validate({ aliases: [this.currentAlias] })
        this.account.aliases.push(this.currentAlias)
        this.$refs.aliasField.reset()
      } catch (error) {
        let errorMsg = null
        if (error.response.data.aliases) {
          errorMsg = error.response.data.aliases
        } else if (error.response.data.non_field_errors) {
          errorMsg = error.response.data.non_field_errors
        }
        this.$refs.observer.setErrors({ alias: errorMsg })
      }
    }
  }
}
</script>
