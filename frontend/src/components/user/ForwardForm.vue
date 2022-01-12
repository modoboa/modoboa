<template>
<div>
  <v-card flat>
    <v-card-text>
      <label class="m-label"><translate>Recipient(s)</translate></label>
      <v-textarea
        v-model="form.recipients"
        :hint="'Indicate one or more recipients separated by a comma (,)'|translate"
        persistent-hint
        rows="3"
        outlined
        />
      <v-checkbox
        v-model="form.keepcopies"
        :label="'Keep local copies'|translate"
        :hint="'Forward messages and store copies into your local mailbox'|translate"
        persistent-hint
        />
    </v-card-text>
    <v-card-actions class="pa-4">
      <v-btn
        color="success"
        :loading="loading"
        @click="submit"
        >
        <translate>Update</translate>
      </v-btn>
    </v-card-actions>
  </v-card>
</div>
</template>

<script>
import account from '@/api/account'
import { bus } from '@/main'

export default {
  props: {
    account: Object
  },
  data () {
    return {
      form: {},
      loading: false
    }
  },
  methods: {
    submit () {
      this.loading = true
      account.setForward(this.form).then(resp => {
        this.loading = false
        bus.$emit('notification', { type: 'success', msg: this.$gettext('Forward updated') })
      })
    }
  },
  mounted () {
    account.getForward().then(resp => {
      this.form = resp.data
    })
  }
}
</script>
