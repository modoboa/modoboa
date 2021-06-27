<template>
<validation-observer ref="observer">
  <v-switch
    v-if="!alias.pk"
    v-model="alias.random"
    :label="'Random address'|translate"
    />
  <validation-provider
    v-if="!alias.random"
    v-slot="{ errors }"
    name="address"
    rules="required"
    >
    <label class="m-label">{{ $gettext('Email address') }}</label>
    <email-field
      ref="address"
      v-model="alias.address"
      :error-messages="errors"
      type="email"
      outlined
      dense
      />
  </validation-provider>
  <validation-provider
    v-if="alias.random"
    v-slot="{ errors }"
    rules="required"
    >
    <label class="m-label">{{ $gettext('Domain') }}</label>
    <v-select
      v-model="alias.domain"
      :items="domains"
      :error-messages="errors"
      item-text="name"
      return-object
      outlined
      dense
      @change="updateAddress"
      />
  </validation-provider>
  <v-switch
    v-model="alias.enabled"
    :label="'Enabled'|translate"
    />
  <label class="m-label">{{ $gettext('Expire at') }}</label>
  <v-text-field
    v-model="alias.expire"
    outlined
    dense
    />
  <label class="m-label">{{ $gettext('Description') }}</label>
  <v-textarea
    v-model="alias.description"
    rows="2"
    outlined
    dense
    />

</validation-observer>
</template>

<script>
import { mapGetters } from 'vuex'
import aliases from '@/api/aliases'
import EmailField from '@/components/tools/EmailField'

export default {
  components: {
    EmailField
  },
  props: ['alias'],
  computed: {
    ...mapGetters({
      domains: 'identities/domains'
    })
  },
  methods: {
    updateAddress (value) {
      aliases.getRandomAddress().then(resp => {
        this.$set(this.alias, 'address', `${resp.data.address}@${value.name}`)
      })
    }
  },
  watch: {
    alias (val) {
      console.log(val)
    }
  }
}
</script>
