<template>
<div class="d-flex justify-center inner">
  <v-stepper v-model="currentStep">
    <v-stepper-header class="align-center px-10">
      <v-img
        src="../../assets/Modoboa_RVB-BLEU-SANS.png"
        max-width="190"
        />
      <v-stepper-step
        v-for="(step, index) in steps"
        :key="index"
        :complete="currentStep > index + 1" :step="index + 1">
        {{ step.title }}
      </v-stepper-step>
      <v-stepper-step :step="steps.length + 1">
        <translate>Summary</translate>
      </v-stepper-step>
      <v-btn icon @click="close">
        <v-icon color="primary" x-large>mdi-close</v-icon>
      </v-btn>
    </v-stepper-header>
    <v-stepper-items class="mt-4 d-flex justify-center">
      <v-stepper-content
        v-for="(step, index) in steps"
        :key="index"
        :step="index + 1"
        class="flex-grow-0"
        >
        <div class="mb-6 text-h5">
          <span class="grey--text text--darken-1">{{ title }}</span> /
          {{ step.title }}
        </div>
        <slot :name="`form.${step.name}`" v-bind:step="index + 1" />
        <div class="d-flex justify-end mt-4">
          <v-btn v-if="index + 1 > 1" @click="currentStep = index" class="mr-10" text>
            <translate>Back</translate>
          </v-btn>
          <v-btn
            color="primary"
            @click="goToNextStep(index + 1, index + 2)"
            large
            >
            <translate>Next</translate>
          </v-btn>
        </div>
      </v-stepper-content>
      <v-stepper-content :step="steps.length + 1" class="flex-grow-0">
        <div class="text-center text-h3"><translate>Summary</translate></div>
        <creation-summary
          :sections="summarySections"
          @modify-step="val => currentStep = val"
          >
          <template v-for="(_, slot) of $scopedSlots" v-slot:[slot]="scope">
            <slot :name="slot" v-bind="scope" />
          </template>
        </creation-summary>
        <div class="d-flex justify-center mt-8">
          <v-btn
            color="primary"
            @click="$emit('create')"
            large
            >
            <translate>Confirm and create</translate>
          </v-btn>
        </div>
      </v-stepper-content>
    </v-stepper-items>
  </v-stepper>
  <confirm-dialog ref="confirm" />
</div>
</template>

<script>
import ConfirmDialog from '@/components/layout/ConfirmDialog'
import CreationSummary from '@/components/tools/CreationSummary'

export default {
  components: {
    ConfirmDialog,
    CreationSummary
  },
  props: {
    title: String,
    steps: Array,
    summarySections: Array,
    formObserverGetter: Function,
    validateObject: Function
  },
  data () {
    return {
      currentStep: 1
    }
  },
  methods: {
    async close (withConfirm) {
      if (withConfirm) {
        const confirm = await this.$refs.confirm.open(
          this.$gettext('Warning'),
          this.$gettext('If you close this form now, your modifications won\'t be saved. Do you confirm?'),
          {
            color: 'warning',
            agreeLabel: this.$gettext('Yes'),
            cancelLabel: this.$gettext('No')
          }
        )
        if (!confirm) {
          return
        }
      }
      this.currentStep = 1
      this.steps.forEach((item, index) => {
        const observer = this.formObserverGetter(index + 1)
        if (observer !== undefined) {
          observer.reset()
        }
      })
      this.$emit('close')
    },
    async goToNextStep (current, next) {
      const observer = this.formObserverGetter(current)
      if (observer !== undefined) {
        const valid = await observer.validate()
        if (!valid) {
          return
        }
        try {
          await this.validateObject()
        } catch (error) {
          observer.setErrors(error.response.data)
          return
        }
      }
      this.currentStep = next
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
</style>
