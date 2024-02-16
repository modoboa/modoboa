<template>
  <div
    class="text-subtitle-1 text-grey-darken-1 mb-5"
    :class="{ 'label--disabled': disabled }"
  >
    <label class="m-label">{{ label }}</label>
  </div>
  <v-input v-model="currentChoice" :rules="[!!disabled || rules.required]">
    <template #default>
      <v-row v-for="(lineChoices, i) in formatedChoices" :key="i" class="ml-5">
        <v-col
          v-for="(choice, j) in lineChoices"
          :key="j"
          class="choice rounded pa-md-10 pa-5 mr-5 flex-grow-0 mb-5"
          :class="{
            'choice--disabled': disabled,
            'choice--selected': !disabled && currentChoice === choice.value,
          }"
          align="center"
          @click="selectChoice(choice.value)"
        >
          <v-row align="center" justify="center">
            <v-col cols="12" class="pa-0">
              <v-icon
                v-if="choice.icon"
                class="hidden-md-and-down mb-5 align-center"
                :color="iconColor(choice.value)"
                size="x-large"
              >
                {{ choice.icon }}
              </v-icon>
            </v-col>
          </v-row>
          <v-row align="center" justify="center">
            <v-col cols="12" class="pa-0">
              <div class="text-grey-darken-1">{{ choice.label }}</div>
            </v-col>
          </v-row>
        </v-col>
      </v-row>
    </template>
    <template #message="{ message }"
      ><div class="ml-4">{{ message }}</div></template
    >
  </v-input>
</template>

<script setup lang="js">
import { ref, onMounted, computed } from 'vue'
import rules from '@/plugins/rules.js'

const props = defineProps({
  modelValue: { type: [Number, String], default: null },
  label: { type: String, default: '' },
  choices: { type: Array, default: () => [] },
  disabled: {
    type: Boolean,
    default: false,
  },
  choicesPerLine: { type: Number, default: undefined },
})

const emit = defineEmits(['update:modelValue'])

const currentChoice = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    emit('update:modelValue', value)
  },
})

const formatedChoices = ref([])

function formatChoices() {
  if (props.choicesPerLine) {
    let sliceIndex = 0
    while (sliceIndex < props.choices.length) {
      const result = props.choices.slice(
        sliceIndex,
        sliceIndex + props.choicesPerLine
      )
      formatedChoices.value.push(result)
      sliceIndex += props.choicesPerLine
    }
  } else {
    formatedChoices.value.push(props.choices)
  }
}

function iconColor(value) {
  return !props.disabled && value === currentChoice.value ? 'primary' : ''
}
function selectChoice(value) {
  if (props.disabled) {
    return
  }
  currentChoice.value = value
}

onMounted(() => {
  formatChoices()
})
</script>

<style lang="scss" scoped>
.choice {
  // width: 200px;
  flex-basis: 200px;
  background-color: #f2f5f7;
  border: 1px solid #dbdddf;
  cursor: pointer;

  &--selected {
    border-color: #046bf8 !important;
  }

  &--disabled {
    cursor: unset;
    opacity: 0.5;
  }
}
.label--disabled {
  opacity: 0.5;
}
</style>
