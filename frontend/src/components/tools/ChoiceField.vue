<template>
<div>
  <div class="text-subtitle-1 grey--text text--darken-1 mb-4"><translate>{{ label }}</translate></div>
  <div class="d-flex">
    <div v-for="(choice, index) in choices"
         :key="index"
         class="choice rounded pa-10 mr-4 text-center"
         :class="{ 'choice--selected': currentChoice === choice.value }"
         @click="selectChoice(choice.value)">
      <v-icon v-if="choice.icon" class="d-block mb-2" :color="iconColor(choice.value)" x-large>{{ choice.icon }}</v-icon>
      <translate class="grey--text text--darken-1">{{ choice.label }}</translate>
    </div>
  </div>
</div>
</template>

<script>
export default {
  props: ['value', 'label', 'choices'],
  data () {
    return {
      currentChoice: this.value
    }
  },
  methods: {
    iconColor (value) {
      return (value === this.currentChoice) ? 'primary' : ''
    },
    selectChoice (value) {
      this.currentChoice = value
      this.$emit('input', value)
    }
  }
}
</script>

<style lang="scss" scoped>
.choice {
  width: 200px;
  background-color: #F2F5F7;
  border: 1px solid #DBDDDF;
  cursor: pointer;

  &--selected {
    border-color: #046BF8 !important;
  }
}
</style>
