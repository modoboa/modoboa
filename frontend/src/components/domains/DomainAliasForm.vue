<template>
<v-card>
  <v-card-title>
    <span class="headline">{{ title }}</span>
  </v-card-title>
  <v-card-text>
    <validation-observer ref="observer">
      <validation-provider
        v-slot="{ errors }"
        name="name"
        rules="required"
        >
        <v-text-field
          v-model="form.name"
          :label="'Name' | translate"
          :error-messages="errors"
          />
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        name="target"
        rules="required"
        >
        <v-select
          v-model="form.target"
          :items="domains"
          item-text="name"
          item-value="pk"
          :label="'Choose a domain' | translate"
          :error-messages="errors"
          single-line
          />
      </validation-provider>
      <v-switch
        v-model="form.enabled"
        label="Enabled"
        color="primary"
        />
    </validation-observer>
  </v-card-text>
  <v-card-actions>
    <v-spacer></v-spacer>
    <v-btn
      color="gray darken-1"
      text
      @click="close"
      >
      Close
    </v-btn>
    <v-btn
      color="primary darken-1"
      text
      @click="submit"
      >
      {{ submitLabel }}
    </v-btn>
  </v-card-actions>
</v-card>
</template>

<script>
import { mapGetters } from 'vuex'
import { bus } from '@/main'

export default {
  props: {
    domainAlias: Object
  },
  computed: {
    ...mapGetters({
      domains: 'domains/domains'
    }),
    submitLabel () {
      return (this.domainAlias) ? 'Update' : 'Add'
    },
    title () {
      return (this.domainAlias) ? 'Edit domain alias' : 'Add a new domain alias'
    }
  },
  data () {
    return {
      form: {
        enabled: true
      }
    }
  },
  methods: {
    close () {
      this.$emit('close')
      this.form = {}
    },
    async submit () {
      const valid = await this.$refs.observer.validate()
      if (!valid) {
        return
      }
      try {
        if (!this.form.pk) {
          await this.$store.dispatch('domains/addDomainAlias', this.form).then(resp => {
            bus.$emit('notification', { msg: this.$gettext('Domain alias created') })
            this.close()
          })
        } else {
          const data = JSON.parse(JSON.stringify(this.form))
          data.target = data.target.pk
          await this.$store.dispatch('domains/updateDomainAlias', { id: this.form.pk, data: data }).then(resp => {
            bus.$emit('notification', { msg: this.$gettext('Domain alias updated') })
            this.close()
          })
        }
      } catch (error) {
        this.$refs.observer.setErrors(error.response.data)
      }
    }
  },
  mounted () {
    if (this.domainAlias) {
      this.form = JSON.parse(JSON.stringify(this.domainAlias))
    }
  },
  watch: {
    domainAlias (value) {
      if (value) {
        this.form = JSON.parse(JSON.stringify(value))
      }
    }
  }
}
</script>
