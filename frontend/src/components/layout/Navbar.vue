<template>
  <v-navigation-drawer
    v-model="drawer"
    app
    clipped
  >
    <v-list dense>
      <template v-for="item in items">
        <v-list-item
          v-if="!item.children"
          :to="item.to"
          link
          :key="item.title"
          >
          <v-list-item-icon v-if="item.icon">
            <v-icon>{{ item.icon }}</v-icon>
          </v-list-item-icon>

          <v-list-item-content>
            <v-list-item-title>{{ item.text }}</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-group v-else
                      :key="item.text"
                      :prepend-icon="item.icon"
                      no-action>
          <template v-slot:activator>
            <v-list-item-title>{{ item.text }}</v-list-item-title>
          </template>

          <template v-for="subitem in item.children">
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
    </v-list>
  </v-navigation-drawer>
</template>

<script>
// import * as api from '@/api'

export default {
  data () {
    return {
      drawer: true,
      items: [
        {
          text: this.$gettext('Dashboard'),
          icon: 'mdi-view-dashboard'
        },
        {
          text: this.$gettext('Domains'),
          to: { name: 'DomainList' },
          icon: 'mdi-domain'
        },
        {
          text: this.$gettext('Identities'),
          icon: 'mdi-account'
        },
        {
          icon: 'mdi-magnify',
          text: this.$gettext('Logs'),
          to: { name: 'LogList' }
        },
        {
          icon: 'mdi-cog',
          text: this.$gettext('Parameters'),
          children: []
        }
      ]
    }
  },
  created () {
    this.$axios.get('/parameters/applications/').then(response => {
      response.data.forEach(item => {
        this.items[4].children.push({
          text: item.label,
          to: { name: 'ParametersEdit', params: { app: item.name } }
        })
      })
    })
  }
}
</script>
