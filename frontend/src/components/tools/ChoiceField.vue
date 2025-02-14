<template>
  <div
    class="text-subtitle-1 text-grey-darken-1 mb-5"
    :class="{ 'label--disabled': disabled }"
  >
    <label class="m-label">{{ label }}</label>
  </div>
  <div
    v-for="(lineChoices, index1) in formatedChoices"
    :key="index1"
    class="d-flex"
  >
    <div
      v-for="(choice, index2) in lineChoices"
      :key="index2"
      class="choice rounded pa-10 mr-4 text-center flex-grow-0 mb-4"
      :class="{
        'choice--disabled': disabled,
        'choice--selected': !disabled && currentChoice === choice.value,
      }"
      @click="selectChoice(choice.value)"
    >
      <v-icon
        v-if="choice.icon"
        class="d-block mb-2 mx-auto"
        :color="iconColor(choice.value)"
        size="x-large"
        :icon="choice.icon"
      />
      <span class="text-grey-darken-1">{{ choice.label }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'

const props = defineProps({
  modelValue: { type: [Number, String], default: null },
  label: { type: String, default: '' },
  choices: { type: Array, default: () => [] },
  disabled: {
    type: Boolean,
    default: false,
  },
  choicesPerLine: {
    type: Number,
    required: false,
    default: null,
  },
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
