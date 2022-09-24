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
                  <translate>Address: </translate> {{ editedAlias.address }}
                </v-col>
                <v-col cols="6">
                  <translate class="mr-2">Enabled</translate>
                  <v-icon color="success" v-if="editedAlias.enabled">mdi-check-circle-outline</v-icon>
                  <v-icon v-else>mdi-close-circle-outline</v-icon>
                </v-col>
              </v-row>
            </v-fade-transition>
          </v-col>
        </v-row>
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <alias-general-form ref="generalForm" v-model="editedAlias" />
      </v-expansion-panel-content>
    </v-expansion-panel>
    <v-expansion-panel>
      <v-expansion-panel-header v-slot="{ open }">
        <v-row no-gutters>
          <v-col cols="4">
            <translate>Recipients</translate>
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
                <v-chip
                  v-for="(rcpt, index) in editedAlias.recipients"
                  :key="index"
                  small
                  >
                  {{ rcpt }}
                </v-chip>
              </v-row>
            </v-fade-transition>
          </v-col>
        </v-row>
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <alias-recipient-form ref="recipientForm" v-model="editedAlias.recipients" />
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
import aliases from '@/api/aliases'
import AliasGeneralForm from './AliasGeneralForm'
import AliasRecipientForm from './AliasRecipientForm'

export default {
  components: {
    AliasGeneralForm,
    AliasRecipientForm
  },
  props: ['alias'],
  data () {
    return {
      editedAlias: {},
      panel: 0
    }
  },
  methods: {
    async save () {
      if (this.$refs.generalForm !== undefined) {
        const valid = await this.$refs.generalForm.$refs.observer.validate()
        if (!valid) {
          return
        }
      }
      try {
        await aliases.patch(this.editedAlias.pk, this.editedAlias).then(resp => {
          bus.$emit('notification', { msg: this.$gettext('Alias updated') })
        })
      } catch (error) {
        if (this.$refs.generalForm) {
          this.$refs.generalForm.$refs.observer.setErrors(error.response.data)
        }
      }
    }
  },
  watch: {
    alias: {
      handler: function (val) {
        if (val) {
          this.editedAlias = { ...val }
        }
      },
      immediate: true
    }
  }
}
</script>
