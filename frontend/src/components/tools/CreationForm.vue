<template>
  <div class="d-flex justify-center inner fill-height">
    <v-stepper v-model="currentStep" :mobile="!smAndDown">
      <ConfirmDialog ref="confirm" />
      <v-stepper-header class="align-center px-10">
        <v-img
          src="@/assets/Modoboa_RVB-BLEU-SANS.png"
          max-width="190"
          class="hidden-sm-and-down"
        />
        <v-stepper-item
          v-for="(step, index) in steps"
          :key="step.name"
          color="primary"
          :value="index + 1"
          :complete="currentStep > index + 1"
        >
          {{ step.title }}
        </v-stepper-item>
        <v-stepper-item :value="steps.length + 1">
          {{ $gettext('Summary') }}
        </v-stepper-item>
        <v-btn
          icon="mdi-close"
          color="primary"
          :size="smAndDown ? 'small' : 'x-large'"
          variant="text"
          @click="close"
        >
        </v-btn>
      </v-stepper-header>
      <v-stepper-window class="mt-4 d-flex justify-center">
        <v-stepper-window-item
          v-for="(step, index) in steps"
          :key="step.name"
          :value="index + 1"
          class="flex-grow-1 ma-10"
        >
          <v-container fluid>
            <v-row align="center" justify="center">
              <v-col cols="8" align="start">
                <div class="mb-5 text-h5">
                  <span class="text-grey-darken-1">{{ title }}</span>
                  /
                  {{ step.title }}
                </div>
                <slot
                  :name="`form.${step.name}`"
                  :step="step"
                  :current-step="index + 1"
                />
              </v-col>
            </v-row>
          </v-container>
          <div class="d-flex justify-end mt-4">
            <v-btn
              v-if="index + 1 > 1"
              class="mr-10"
              variant="text"
              @click="currentStep = index"
            >
              {{ $gettext('Back') }}
            </v-btn>
            <v-btn
              color="primary"
              size="large"
              @click="goToNextStep(index + 1, index + 2)"
            >
              {{ $gettext('Next') }}
            </v-btn>
          </div>
        </v-stepper-window-item>
        <v-stepper-window-item :value="steps.length + 1" class="flex-grow-0">
          <div class="text-center text-h3">
            {{ $gettext('Summary') }}
          </div>
          <CreationSummary
            :sections="summarySections"
            @modify-step="(val) => (currentStep = val)"
          >
            <template v-for="(_, slot) of $slots" #[slot]="scope">
              <slot :name="slot" v-bind="scope" />
            </template>
          </CreationSummary>
          <div class="d-flex justify-center mt-8">
            <v-btn
              color="primary"
              size="large"
              :loading="working"
              @click="create"
            >
              {{ $gettext('Confirm and create') }}
            </v-btn>
          </div>
        </v-stepper-window-item>
      </v-stepper-window>
    </v-stepper>
  </div>
</template>

<script setup lang="js">
import ConfirmDialog from './ConfirmDialog'
import CreationSummary from './CreationSummary.vue'
import { ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useDisplay } from 'vuetify'

const { smAndDown } = useDisplay()

const props = defineProps({
  title: { type: String, default: '' },
  steps: { type: Array, default: () => [] },
  summarySections: { type: Array, default: () => [] },
  getVFormRef: { type: Function, default: null },
  formGetter: { type: Function, default: null },
  validateObject: { type: Function, default: null },
})

const currentStep = ref(1)
const working = ref(false)
const confirm = ref()

const emit = defineEmits(['close', 'create', 'validationError'])

const { $gettext } = useGettext()

async function close() {
  const confirmed = await confirm.value.open(
    $gettext('Warning'),
    $gettext(
      "If you close this form now, your modifications won't be saved. Do you confirm?"
    ),
    {
      color: 'warning',
      agreeLabel: $gettext('Yes'),
      cancelLabel: $gettext('No'),
    }
  )
  if (!confirmed) {
    return
  }
  emit('close')
}
async function goToNextStep(current, next) {
  const vform = props.getVFormRef(props.steps[current - 1])
  if (vform !== undefined) {
    const { valid } = await vform.validate()
    if (!valid) {
      return
    }
    if (props.validateObject) {
      try {
        await props.validateObject()
      } catch (error) {
        emit('validationError', current, error.response.data)
        return
      }
    }
  }
  currentStep.value = next
}

function create() {
  working.value = true
  emit('create')
}
</script>

<style lang="scss">
.inner {
  background-color: #fff;
}
.v-stepper {
  width: 100%;
  overflow: auto;
}

.v-window {
  &__container {
    width: 60%;
  }
}
</style>
