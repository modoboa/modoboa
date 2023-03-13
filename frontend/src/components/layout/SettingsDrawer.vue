<template>
<v-list-group
              color="white"
              :key="settings.text"
              :prepend-icon="settings.icon"
              no-action>
  <template v-slot:activator>
    <v-list-item-title>{{ settings.title }}</v-list-item-title>
  </template>

  <template v-for="subitem in settings.children">
    <v-list-item v-if="!subitem.children"
                  :key="subitem.text"
                  :to="subitem.to"
                  link>
      <v-list-item-content>
        <v-list-item-title>{{ subitem.text }}</v-list-item-title>
      </v-list-item-content>
    </v-list-item>
    <v-list-group v-else
                  :key="subitem.text"
                  :value="true"
                  no-action
                  sub-group>
      <template v-slot:activator>
        <v-list-item-title>{{ subitem.text }}</v-list-item-title>
      </template>
      <v-list-item v-for="subsubitem in subitem.children"
                    :key="subsubitem.text"
                    :to="subsubitem.to"
                    link>
        <v-list-item-title>{{ subsubitem.text }}</v-list-item-title>
      </v-list-item>
    </v-list-group>
  </template>
</v-list-group>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  props: ['parametersList', 'extension'],
  computed: {
    ...mapGetters({
      authUser: 'auth/authUser'
    }),
    settings () {
      const menu = this.settingMenu
      this.parametersList.forEach(item => {
        if (item.is_extension === this.extension) {
          menu.children.push({
            text: item.label,
            to: { name: 'ParametersEdit', params: { app: item.name } }
          })
        }
      })
      return menu
    }
  },
  data () {
    return {
      settingMenu:
      {
        title: this.$gettext('Settings'),
        icon: 'mdi-cog',
        children: [],
        roles: ['SuperAdmins']
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.v-list-item {
  &--active {
    &::before {
      opacity: 0;
    }
    background-color: #034bad;
    color: white;
    opacity: 1;
  }
}
</style>
