<template>
<div>
  <div class="text-subtitle-1 grey--text text--darken-1 mb-4" :class="{ 'label--disabled': disabled }">
    <label class="m-label">{{ label }}</label>
  </div>
  <div class="d-flex" v-for="(lineChoices, index1) in formatedChoices" :key="index1">
    <div v-for="(choice, index2) in lineChoices"
         :key="index2"
         class="choice rounded pa-10 mr-4 text-center flex-grow-0 mb-4"
         :class="{ 'choice--disabled': disabled, 'choice--selected': !disabled && currentChoice === choice.value }"
         @click="selectChoice(choice.value)"
         >
      <v-icon v-if="choice.icon" class="d-block mb-2" :color="iconColor(choice.value)" x-large>{{ choice.icon }}</v-icon>
      <span class="grey--text text--darken-1">{{ choice.label }}</span>
    </div>
  </div>
</div>
</template>

<script>
export default {
  props: {
    value: [Number, String],
    label: String,
    choices: Array,
    disabled: {
      type: Boolean,
      default: false
    },
    choicesPerLine: Number
  },
  data () {
    return {
      currentChoice: null,
      formatedChoices: []
    }
  },
  methods: {
    formatChoices () {
      if (this.choicesPerLine) {
        let sliceIndex = 0
        while (sliceIndex < this.choices.length) {
          const result = this.choices.slice(sliceIndex, sliceIndex + this.choicesPerLine)
          this.formatedChoices.push(result)
          sliceIndex += this.choicesPerLine
        }
      } else {
        this.formatedChoices.push(this.choices)
      }
    },
    iconColor (value) {
      return (!this.disabled && value === this.currentChoice) ? 'primary' : ''
    },
    selectChoice (value) {
      if (this.disabled) {
        return
      }
      this.currentChoice = value
      this.$emit('input', value)
    }
  },
  mounted () {
    this.formatChoices()
  },
  watch: {
    value: {
      handler (val) {
        this.currentChoice = val
      },
      immediate: true
    }
  }
}
</script>

<style lang="scss" scoped>
.choice {
  // width: 200px;
  flex-basis: 200px;
  background-color: #F2F5F7;
  border: 1px solid #DBDDDF;
  cursor: pointer;

  &--selected {
    border-color: #046BF8 !important;
  }

  &--disabled {
    cursor: unset;
    opacity: .5;
  }
}
.label--disabled {
  opacity: .5;
}
</style>
