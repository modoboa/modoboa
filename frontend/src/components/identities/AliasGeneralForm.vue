<template>
<validation-observer ref="observer">
  <v-switch
    v-if="!form.pk"
    v-model="form.random"
    :label="'Random address'|translate"
    @input="update"
    />
  <validation-provider
    v-if="!form.random"
    v-slot="{ errors }"
    name="address"
    rules="required"
    >
    <label class="m-label">{{ $gettext('Email address') }}</label>
    <email-field
      ref="address"
      v-model="form.address"
      :error-messages="errors"
      type="email"
      outlined
      dense
      @input="update"
      />
  </validation-provider>
  <validation-provider
    v-if="form.random"
    v-slot="{ errors }"
    rules="required"
    >
    <label class="m-label">{{ $gettext('Domain') }}</label>
    <v-select
      v-model="form.domain"
      :items="domains"
      :error-messages="errors"
      item-text="name"
      return-object
      outlined
      dense
      @change="updateAddress"
      @input="update"
      />
  </validation-provider>
  <v-switch
    v-model="form.enabled"
    :label="'Enabled'|translate"
    @input="update"
    />
  <label class="m-label">{{ $gettext('Expire at') }}</label>
  <v-text-field
    v-model="form.expire"
    outlined
    dense
    @input="update"
    />
  <label class="m-label">{{ $gettext('Description') }}</label>
  <v-textarea
    v-model="form.description"
    rows="2"
    outlined
    dense
    @input="update"
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
  props: ['value'],
  computed: {
    ...mapGetters({
      domains: 'identities/domains'
    })
  },
  data () {
    return {
      form: {}
    }
  },
  methods: {
    updateAddress (value) {
      aliases.getRandomAddress().then(resp => {
        this.$set(this.form, 'address', `${resp.data.address}@${value.name}`)
        this.update()
      })
    },
    update () {
      this.$emit('input', this.form)
    }
  },
  mounted () {
    this.form = { ...this.value }
  }
}
</script>
