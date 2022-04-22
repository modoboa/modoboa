<template>
<v-card>
  <v-card-title>
    <span class="headline">{{ title }}</span>
  </v-card-title>
  <v-card-text>
    <v-alert
      text
      type="info"
      >
      <translate tag="p">Provide a CSV file where lines respect one of the following formats:</translate>
      <slot name="help" />
      <translate tag="p">The first element of each line is mandatory and must be equal to one of the previous values.</translate>
      <translate tag="p">You can use a different character as separator.</translate>
    </v-alert>
    <validation-observer ref="observer">
      <validation-provider
        v-slot="{ errors }"
        name="name"
        rules="required"
        >
        <label class="m-label"><translate>Select file</translate></label>
        <v-file-input
          v-model="form.sourcefile"
          accept="text/csv"
          :error-messages="errors"
          truncate-length="15"
          outlined
          dense
          />
      </validation-provider>
      <label class="m-label"><translate>Separator</translate></label>
      <v-text-field
        v-model="form.sepchar"
        :error-messages="errors"
        outlined
        dense
        />
      <v-switch
        v-model="form.continue_if_exists"
        :label="'Continue on error'|translate"
        color="primary"
        dense
        :hint="'Don\'t treat duplicated objects as errors'|translate"
        persistent-hint
        />
      <slot name="extraFields" v-bind:form="form" />
    </validation-observer>
  </v-card-text>
  <v-card-actions>
    <v-spacer></v-spacer>
    <v-btn
      @click="close"
      >
      <translate>Close</translate>
    </v-btn>
    <v-btn
      color="primary"
      @click="submit"
      >
      <translate>Import</translate>
    </v-btn>
  </v-card-actions>
</v-card>
</template>

<script>
export default {
  props: {
    helpText: String,
    title: String
  },
  data () {
    return {
      form: {}
    }
  },
  methods: {
    close () {
      this.form = {}
      this.$refs.observer.reset()
      this.$emit('close')
    },
    async submit () {
      const valid = await this.$refs.observer.validate()
      if (!valid) {
        return
      }
      const data = new FormData()
      data.append('sourcefile', this.form.sourcefile)
      if (this.form.sepchar) {
        data.append('sepchar', this.form.sepchar)
      }
      if (this.form.continue_if_exists) {
        data.append('continue_if_exists', this.form.continue_if_exists)
      }
      this.$emit('beforeSubmit', data)
      this.$emit('submit', data)
    }
  }
}
</script>
