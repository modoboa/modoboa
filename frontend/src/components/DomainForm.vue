<template>
  <div>
    <h1 class="title">Add domain</h1>
    <form>
      <b-field label="Name" :type="formErrors && formErrors.name ? 'is-danger' : ''"
               :message="formErrors && formErrors.name ? formErrors.name[0] : ''">
        <b-input v-model="domain.name"></b-input>
      </b-field>
      <b-field label="Quota" :type="formErrors && formErrors.quota ? 'is-danger' : ''"
               :message="formErrors && formErrors.quota ? formErrors.quota[0] : ''">
        <b-input v-model="domain.quota"></b-input>
      </b-field>
      <b-field>
        <button class="button is-primary" @click="saveDomain">Save</button>
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
        }
    }
}
</script>
