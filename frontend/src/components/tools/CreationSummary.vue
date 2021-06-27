<template>
<div>
  <div v-for="(section, index) in sections" :key="index">
    <div class="subtitle mt-4 d-flex">
      <span class="text-h6">{{ section.title }}</span>
      <a href="#" class="edit-link ml-auto" @click="$emit('modify-step', index + 1)"><translate>Modify</translate></a>
    </div>
    <v-row v-for="(item, itemIndex) in section.items"
           :key="itemIndex"
           dense
           >
      <template v-if="item.value !== undefined">
        <slot :name="`item.${item.name}`" v-bind:item="item" v-bind:displayList="displayList">
          <v-col><span class="grey--text">{{ item.key }}</span></v-col>
          <v-col class="text-right" v-if="item.type === 'yesno'">{{ item.value|yesno }}</v-col>
          <v-col class="text-right" v-else-if="item.type === 'list'">
            {{ displayList(item.value) }}
          </v-col>
          <v-col class="text-right" v-else>{{ item.value }}</v-col>
        </slot>
      </template>
    </v-row>
  </div>
</div>
</template>

<script>
export default {
  props: ['sections'],
  methods: {
    displayList (value) {
      return (value.length) ? value.join(', ') : this.$gettext('Empty')
    }
  }
}
</script>

<style scoped lang="scss">
.subtitle {
  color: #000;
  border-bottom: 1px solid #DBDDDF;
}

.edit-link {
  text-decoration: none;
}
</style>
