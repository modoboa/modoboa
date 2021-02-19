<template>
  <v-layout>
    <v-flex>
      <v-card>
        <v-card-title>
          <h1 class="headline"><translate>Edit domain</translate></h1>
        </v-card-title>
        <v-card-text>
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
                          <translate>Name: </translate> {{ editedDomain.name }}
                        </v-col>
                        <v-col cols="6">
                          <translate>Type: </translate> {{ editedDomain.type }}
                        </v-col>
                      </v-row>
                    </v-fade-transition>
                  </v-col>
                </v-row>
              </v-expansion-panel-header>
              <v-expansion-panel-content>
                <domain-general-form ref="generalForm" :domain="editedDomain" />
              </v-expansion-panel-content>
            </v-expansion-panel>
            <v-expansion-panel>
              <v-expansion-panel-header v-slot="{ open }">
                <v-row no-gutters>
                  <v-col cols="4">
                    <translate>DNS</translate>
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
                          <translate class="mr-2">DNS checks</translate>
                          <v-icon color="success" v-if="editedDomain.enable_dns_checks">mdi-check-circle-outline</v-icon>
                          <v-icon v-else>mdi-close-circle-outline</v-icon>
                        </v-col>
                        <v-col cols="6">
                          <translate class="mr-2">DKIM signing</translate>
                          <v-icon color="success" v-if="editedDomain.enable_dkim">mdi-check-circle-outline</v-icon>
                          <v-icon v-else>mdi-close-circle-outline</v-icon>
                        </v-col>
                      </v-row>
                    </v-fade-transition>
                  </v-col>
                </v-row>
              </v-expansion-panel-header>
              <v-expansion-panel-content>
                <domain-dns-form ref="dnsForm" :domain="editedDomain" />
              </v-expansion-panel-content>
            </v-expansion-panel>
            <v-expansion-panel>
              <v-expansion-panel-header v-slot="{ open }">
                <v-row no-gutters>
                  <v-col cols="4">
                    <translate>Limitations</translate>
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
                          <translate class="mr-2">Quota: </translate> {{ domain.quota }}
                        </v-col>
                        <v-col cols="6" v-if="domain.message_sending_limit">
                          <translate class="mr-2">Sending limit: </translate> {{ domain.message_sending_limit }}
                        </v-col>
                        <v-col cols="6" v-else>
                          <translate class="mr-2">No sending limit</translate>
                        </v-col>
                      </v-row>
                    </v-fade-transition>
                  </v-col>
                </v-row>
              </v-expansion-panel-header>
              <v-expansion-panel-content>
                <domain-limitations-form :domain="editedDomain" />
              </v-expansion-panel-content>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey darken-1" text @click="close">
            <translate>Cancel</translate>
          </v-btn>
          <v-btn color="primary darken-1" text @click="save">
            <translate>Save</translate>
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-flex>
  </v-layout>
</template>

<script>
import { bus } from '@/main'
import DomainDNSForm from './DomainDNSForm'
import DomainGeneralForm from './DomainGeneralForm'
import DomainLimitationsForm from './DomainLimitationsForm'

export default {
  components: {
    'domain-dns-form': DomainDNSForm,
    DomainGeneralForm,
    DomainLimitationsForm
  },
  props: ['domain'],
  data () {
    return {
      editedDomain: {},
      panel: 0
    }
  },
  methods: {
    close () {
      this.$emit('close')
      this.editedDomain = {}
      this.panel = 0
    },
    async save () {
      if (this.$refs.generalForm !== undefined) {
        const valid = await this.$refs.generalForm.$refs.observer.validate()
        if (!valid) {
          return
        }
      }
      this.$store.dispatch('domains/updateDomain', this.editedDomain).then(resp => {
        this.close()
        bus.$emit('notification', { msg: this.$gettext('Domain updated') })
      })
    }
  },
  watch: {
    domain: {
      handler: function (val) {
        if (val) {
          this.editedDomain = JSON.parse(JSON.stringify(val))
        }
      },
      immediate: true
    }
  }
}
</script>
