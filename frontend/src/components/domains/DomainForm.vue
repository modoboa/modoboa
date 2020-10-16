<template>
  <v-layout>
    <v-flex>
      <v-card>
        <v-card-title>
          <h1 class="title" v-if="!domain.pk">Add domain</h1>
          <h1 class="title" v-else>Edit domain</h1>
        </v-card-title>
        <v-card-text>
          <v-text-field label="Name"
                        v-model="domain.name"
                        :error="formErrors['name'] !== undefined"
                        :error-messages="formErrors['name']"
          >
          </v-text-field>
          <v-text-field label="Quota"
                        v-model="domain.quota"
                        suffix="MB"
                        :error="formErrors['quota'] !== undefined"
                        :error-messages="formErrors['quota']"
          >
          </v-text-field>
          <v-text-field label="Default mailbox quota"
                        v-model="domain.default_mailbox_quota"
                        suffix="MB"
                        :error="formErrors['default_mailbox_quota']"
                        :error-messages="formErrors['default_mailbox_quota']"
          >
          </v-text-field>
          <v-checkbox label="Enabled"
                      v-model="domain.enabled"
          >
          </v-checkbox>
          <v-checkbox label="Enable DNS checks"
                      v-model="domain.enable_dns_checks"
          >
          </v-checkbox>
          <v-checkbox label="Enable DKIM signing"
                      v-model="domain.enable_dkim"
          >
          </v-checkbox>
          <v-text-field label="DKIM key selector"
                        v-model="domain.dkim_key_selector"
                        v-if="domain.enable_dkim"
          >
          </v-text-field>
          <v-text-field label="DKIM key length"
                        v-model="domain.dkim_key_length"
                        v-if="domain.enable_dkim"
          >
          </v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="blue darken-1" text @click="cancel">
            Cancel
          </v-btn>
          <v-btn color="blue darken-1" text @click="save">
            Save
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-flex>
  </v-layout>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  data () {
    return {
      formErrors: {},
      domain: {}
    }
  },
  computed: {
    ...mapGetters({
      getDomainByPk: 'domains/getDomainByPk'
    })
  },
  mounted () {
    var domainPk = this.$route.params.domainPk
    if (domainPk) {
      if (!this.$store.state.domainsLoaded) {
        this.$store.dispatch('domains/getDomains').then(response => {
          this.loadDomain(domainPk)
        })
      } else {
        this.loadDomain(domainPk)
      }
    }
  },
  methods: {
    loadDomain (pk) {
      this.domain = JSON.parse(
        JSON.stringify(this.getDomainByPk(pk))
      )
    },
    onSaveError (response) {
      this.formErrors = response.data
    },
    save () {
      var action
      var msg
      if (this.domain.pk) {
        action = 'domains/updateDomain'
        msg = 'Domain updated.'
      } else {
        action = 'domains/createDomain'
        msg = 'Domain created.'
      }
      this.$store.dispatch(action, this.domain).then(response => {
        this.$router.push({ name: 'DomainList' })
        this.$toast.open({
          message: msg,
          type: 'is-success',
          position: 'is-bottom'
        })
      }, this.onSaveError)
    },
    cancel () {
      this.$router.push({ name: 'DomainList' })
    }
  }
}
</script>
