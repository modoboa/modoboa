<template>
<div class="d-flex justify-center inner">
  <v-stepper v-model="step">
    <v-stepper-header class="align-center px-10">
      <v-img
        src="../../assets/Modoboa_RVB-BLEU-SANS.png"
        max-width="190"
        />
      <v-stepper-step :complete="step > 1" step="1">
        <translate>General</translate>
      </v-stepper-step>

      <v-stepper-step :complete="step > 2" step="2">
        <translate>Mail</translate>
      </v-stepper-step>
      <v-btn icon @click="close">
        <v-icon color="primary" x-large>mdi-close</v-icon>
      </v-btn>
    </v-stepper-header>
    <v-stepper-items class="mt-4 d-flex justify-center">
      <v-stepper-content step="1" class="flex-grow-0">
        <div class="mb-6 text-h5">
          <translate class="grey--text text--darken-1">New account</translate> /
          <translate>General</translate>
        </div>
        <account-general-form ref="form_1" :account="account" />
        <div class="d-flex justify-end">
          <v-btn
            color="primary"
            @click="goToNextStep(1, 2)"
            large
            >
            <translate>Next</translate>
          </v-btn>
        </div>
      </v-stepper-content>
    </v-stepper-items>
  </v-stepper>
  <confirm-dialog ref="confirm" />
</div>
</template>

<script>
import AccountGeneralForm from './AccountGeneralForm'
import ConfirmDialog from '@/components/layout/ConfirmDialog'

export default {
  components: {
    AccountGeneralForm,
    ConfirmDialog
  },
  data () {
    return {
      account: {},
      step: 1
    }
  },
  methods: {
    async close (withConfirm) {
      if (withConfirm) {
        const confirm = await this.$refs.confirm.open(
          this.$gettext('Warning'),
          this.$gettext('If you close this form now, your modifications won\'t be saved. Do you confirm?'),
          {
            color: 'error'
          }
        )
        if (!confirm) {
          return
        }
      }
      this.$emit('close')
      this.step = 1
    },
    async goToNextStep (current, next) {
      const valid = await this.$refs[`form_${current}`].$refs.observer.validate()
      if (!valid) {
        return
      }
      this.step = next
    }
  }
}
</script>

<style lang="scss">
.inner {
  background-color: #fff;
}
.v-stepper {
  width: 100%;
  overflow: auto;

  &__content {
    width: 60%;
  }

  &__items {
    overflow-y: auto;
  }

  &__wrapper {
    padding: 0 10px;
  }
}
.subtitle {
  color: #000;
  border-bottom: 1px solid #DBDDDF;
}

.edit-link {
  text-decoration: none;
}
</style>
