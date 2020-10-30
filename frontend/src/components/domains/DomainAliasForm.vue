<template>
<v-card>
  <v-card-title>
    <span class="headline">{{ title }}</span>
  </v-card-title>
  <v-card-text>
    <v-text-field v-model="form.name" label="Name" />
    <v-select
      v-model="form.target"
      :items="domains"
      item-text="name"
      item-value="pk"
      label="Choose a domain"
      single-line
      ></v-select>
    <v-switch
      v-model="form.enabled"
      label="Enabled"
      color="primary"
      />
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
    submit () {
      if (!this.form.pk) {
        this.$store.dispatch('domains/addDomainAlias', this.form).then(resp => {
          this.close()
        })
      } else {
        const data = JSON.parse(JSON.stringify(this.form))
        data.target = data.target.pk
        this.$store.dispatch('domains/updateDomainAlias', { id: this.form.pk, data: data }).then(resp => {
          this.close()
        })
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
