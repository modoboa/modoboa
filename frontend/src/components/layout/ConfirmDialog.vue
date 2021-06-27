<template>
<v-dialog
  v-model="dialog"
  :max-width="options.width"
  :style="{ zIndex: options.zIndex }"
  @keydown.esc="cancel"
  >
  <v-card>
    <v-toolbar dark :color="options.color" dense flat>
      <v-toolbar-title class="text-body-2 font-weight-bold">
        {{ title }}
      </v-toolbar-title>
    </v-toolbar>
    <v-card-text
      v-show="!!message"
      class="pa-4"
      >
      {{ message }}
      <slot></slot>
    </v-card-text>
    <v-card-actions class="pt-3">
      <v-spacer></v-spacer>
      <v-btn
        v-if="!options.noconfirm"
        @click.native="cancel"
        >
        {{ options.cancelLabel }}
      </v-btn>
      <v-btn
        :color="this.options.color"
        @click.native="agree">
        {{ options.agreeLabel }}
      </v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
</template>

<script>
export default {
  data () {
    return {
      dialog: false,
      resolve: null,
      reject: null,
      message: null,
      title: null,
      options: {
        color: 'primary',
        width: 400,
        zIndex: 200,
        noconfirm: false,
        cancelLabel: this.$gettext('Cancel'),
        agreeLabel: this.$gettext('OK')
      }
    }
  },
  methods: {
    open (title, message, options) {
      this.dialog = true
      this.title = title
      this.message = message
      this.options = Object.assign(this.options, options)
      return new Promise((resolve, reject) => {
        this.resolve = resolve
        this.reject = reject
      })
    },
    agree () {
      this.resolve(true)
      this.dialog = false
    },
    cancel () {
      this.resolve(false)
      this.dialog = false
    }
  }
}
</script>
