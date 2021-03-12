<template>
<v-chip :color="chipType" small>
  {{ label }}
</v-chip>
</template>

<script>
export default {
  props: ['status'],
  computed: {
    label () {
      if (this.status === 'disabled') {
        return this.$gettext('Disabled')
      }
      if (this.status === 'pending') {
        return this.$gettext('Pending')
      }
      if (this.status === 'critical') {
        return this.$gettext('Problem')
      }
      if (this.status === 'ok') {
        return this.$gettext('Valid')
      }
      return this.$gettext('Unknown')
    },
    chipType () {
      if (this.status === 'disabled') {
        return ''
      }
      if (this.status === 'pending') {
        return 'info'
      }
      if (this.status === 'critical') {
        return 'error'
      }
      if (this.status === 'ok') {
        return 'success'
      }
      return 'warning'
    }
  }
}
</script>
