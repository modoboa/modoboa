<template>
<div>
  <v-expansion-panels v-model="panel">
    <v-expansion-panel>
      <v-expansion-panel-header v-slot="{ open }">
        <v-row no-gutters>
          <v-col cols="4">
            <translate>General</translate>
          </v-col>
          <v-col
            cols="8"
            class="text--secondary"
            >
            <v-fade-transition leave-absolute>
              <span v-if="open"></span>
              <v-row
                v-else
                no-gutters
                style="width: 100%"
                >
                <v-col cols="6">
                  <translate>Name: </translate> {{ editedProvider.name }}
                </v-col>
              </v-row>
            </v-fade-transition>
          </v-col>
        </v-row>
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <provider-general-form ref="generalForm" v-model="editedProvider" />
      </v-expansion-panel-content>
    </v-expansion-panel>
    <v-expansion-panel>
      <v-expansion-panel-header v-slot="{ open }">
        <v-row no-gutters>
          <v-col cols="4">
            <translate>Associated domains</translate>
          </v-col>
          <v-col
            cols="8"
            class="text--secondary"
            >
            <v-fade-transition leave-absolute>
              <span v-if="open"></span>
              <v-row
                v-else
                no-gutters
                style="width: 100%"
                >
                <v-col v-if="editedProvider.domains.length > 0" cols="6">
                 <translate>Number of associated domains: </translate> {{ editedProvider.domains.length }}
                </v-col>
                <v-col v-else cols="6">
                 <translate>No associated domains</translate>
                </v-col>
              </v-row>
            </v-fade-transition>
          </v-col>
        </v-row>
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <provider-associated-form ref="associatedForm" v-model="editedProvider.domains" />
      </v-expansion-panel-content>
    </v-expansion-panel>
  </v-expansion-panels>
  <div class="mt-4 d-flex justify-end">
    <v-btn @click="$router.go(-1)">
      <translate>Cancel</translate>
    </v-btn>
    <v-btn class="ml-4" color="primary darken-1" @click="save">
      <translate>Save</translate>
    </v-btn>
  </div>
</div>
</template>

<script>
import { bus } from '@/main'
import providers from '@/api/imap_migration/providers'
import ProviderGeneralForm from './ProviderGeneralForm'
import ProviderAssociatedForm from './ProviderAssociatedForm'

export default {
  components: {
    ProviderGeneralForm,
    ProviderAssociatedForm
  },
  props: ['provider'],
  data () {
    return {
      editedProvider: {},
      panel: 0
    }
  },
  methods: {
    async save () {
      if (this.$refs.generalForm !== undefined) {
        const valid = await this.$refs.generalForm.validateForm()
        if (!valid) {
          return
        }
      }
      if (this.$refs.associatedForm !== undefined) {
        const valid = await this.$refs.associatedForm.validateForm()
        if (!valid) {
          return
        }
      }
      try {
        const data = { ...this.editedProvider }
        data.domains = []
        for (const domain of this.editedProvider.domains) {
          if (domain.new_domain) {
            data.domains.push({
              name: domain.name,
              new_domain: domain.new_domain.pk || domain.new_domain.id
            })
          } else {
            data.domains.push(domain)
          }
        }
        await providers.patchProvider(this.editedProvider.id, data).then(() => {
          bus.$emit('notification', { msg: this.$gettext('Provider updated') })
          this.$store.dispatch('providers/getProviders')
          this.$router.push({ name: 'ProvidersList' })
        })
      } catch (error) {
        if (this.$refs.generalForm) {
          this.$refs.generalForm.$refs.observer.setErrors(error.response.data)
        }
        if (this.$refs.associatedForm) {
          this.$refs.associatedForm.$refs.observer.setErrors(error.response.data)
        }
      }
    }
  },
  watch: {
    provider: {
      handler: function (val) {
        if (val) {
          this.editedProvider = { ...val }
          if (!this.editedProvider.domains) {
            this.editedProvider.domains = []
          }
        }
      },
      immediate: true
    }
  }
}
</script>
