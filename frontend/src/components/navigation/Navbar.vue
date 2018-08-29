<template>
  <v-navigation-drawer
      :clipped="$vuetify.breakpoint.lgAndUp"
      v-model="drawer"
      app
  >
    <v-list dense>
      <template v-for="item in items">
        <v-layout
            v-if="item.heading"
            :key="item.heading"
            row
            align-center
        >
          <v-flex xs6>
            <v-subheader v-if="item.heading">
              {{ item.heading }}
            </v-subheader>
          </v-flex>
          <v-flex xs6 class="text-xs-center">
            <a href="#!" class="body-2 black--text">EDIT</a>
          </v-flex>
        </v-layout>
        <v-list-group
            v-else-if="item.children"
            v-model="item.model"
            :key="item.text"
            :prepend-icon="item.icon"
            :append-icon="item['icon-alt']"
        >
          <v-list-tile slot="activator">
            <v-list-tile-content>
              <v-list-tile-title>
                {{ item.text }}
              </v-list-tile-title>
            </v-list-tile-content>
          </v-list-tile>
          <v-list-tile
              v-for="(child, i) in item.children"
              :key="i"
              :to="child.to"
          >
            <v-list-tile-action v-if="child.icon">
              <v-icon>{{ child.icon }}</v-icon>
            </v-list-tile-action>
            <v-list-tile-content>
              <v-list-tile-title>
                {{ child.text }}
              </v-list-tile-title>
            </v-list-tile-content>
          </v-list-tile>
        </v-list-group>
        <v-list-tile v-else :key="item.text" :to="item.to">
          <v-list-tile-action>
            <v-icon>{{ item.icon }}</v-icon>
          </v-list-tile-action>
          <v-list-tile-content>
            <v-list-tile-title>
              {{ item.text }}
            </v-list-tile-title>
          </v-list-tile-content>
        </v-list-tile>
      </template>
    </v-list>
  </v-navigation-drawer>
</template>

<script>
import * as api from '@/api'

export default {
    data () {
        return {
            drawer: true,
            items: [
                {
                    text: 'Dashboard',
                    icon: 'dashboard'
                },
                {
                    text: 'Domains',
                    to: { name: 'DomainList' },
                    icon: 'domain'
                },
                {
                    text: 'Identities',
                    icon: 'account_box'
                },
                {
                    icon: 'search',
                    text: 'Logs'
                },
                {
                    icon: 'settings',
                    text: 'Parameters',
                    children: []
                }
            ]
        }
    },
    created () {
        api.getParametersApplications().then(response => {
            response.data.forEach(item => {
                this.items[4].children.push({
                    text: item.label,
                    to: { name: 'ParametersEdit', params: {app: item.name} }
                })
            })
        })
    }
}
</script>
