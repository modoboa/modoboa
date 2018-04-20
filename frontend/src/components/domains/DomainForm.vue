<template>
  <div>
    <h1 class="title">Add domain</h1>
    <form>
      <b-field label="Name" :type="formErrors && formErrors.name ? 'is-danger' : ''"
               :message="formErrors && formErrors.name ? formErrors.name[0] : ''"
               horizontal>
        <b-input v-model="domain.name"></b-input>
      </b-field>
      <b-field label="Quota" :type="formErrors && formErrors.quota ? 'is-danger' : ''"
               :message="formErrors && formErrors.quota ? formErrors.quota[0] : ''"
               horizontal>
        <b-input v-model="domain.quota"></b-input>
        <p class="control">
          <span class="button is-static">MB</span>
        </p>
      </b-field>
      <b-field label="Default mailbox quota"
               :type="formErrors && formErrors.default_mailbox_quota ? 'is-danger' : ''"
               :message="formErrors && formErrors.default_mailbox_quota ? formErrors.default_mailbox_quota[0] : ''"
               horizontal>
        <b-input v-model="domain.default_mailbox_quota"></b-input>
        <p class="control">
          <span class="button is-static">MB</span>
        </p>
      </b-field>
      <b-field label="Enabled" horizontal>
        <b-checkbox v-model="domain.enabled"></b-checkbox>
      </b-field>
      <b-field label="Enable DNS checks" horizontal>
        <b-checkbox v-model="domain.enable_dns_checks"></b-checkbox>
      </b-field>
      <b-field label="Enable DKIM signing" horizontal>
        <b-checkbox v-model="domain.enable_dkim"></b-checkbox>
      </b-field>
      <b-field label="DKIM key selector" v-if="domain.enable_dkim" horizontal>
        <b-checkbox v-model="domain.dkim_key_selector"></b-checkbox>
      </b-field>
      <b-field label="DKIM keu length" v-if="domain.enable_dkim" horizontal>
        <b-checkbox v-model="domain.dkim_key_length"></b-checkbox>
      </b-field>
      <b-field grouped horizontal>
        <p class="control">
          <button class="button is-primary" @click="saveDomain">Save</button>
        </p>
        <p class="control">
          <button class="button" @click="cancel">Cancel</button>
        </p>
      </b-field>
    </form>
  </div>
</template>

<script>
export default {
    data () {
        return {
            formErrors: {},
            domain: {}
        }
    },
    mounted () {
        var domainPk = this.$route.params.domainPk
        if (domainPk) {
            if (!this.$store.state.domainsLoaded) {
                this.$store.dispatch('getDomains').then(response => {
                    this.loadDomain(domainPk)
                })
            } else {
                this.loadDomain(domainPk)
            }
        }
    },
    methods: {
        loadDomain (pk) {
            this.domain = JSON.parse(JSON.stringify(this.$store.getters.getDomainByPk(pk)))
        },
        onSaveError (response) {
            this.formErrors = response.data
        },
        saveDomain () {
            var action
            var msg
            if (this.domain.pk) {
                action = 'updateDomain'
                msg = 'Domain updated.'
            } else {
                action = 'createDomain'
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

<style>
 form {
     background: #ffffff;
     padding: 20px;
 }
</style>
