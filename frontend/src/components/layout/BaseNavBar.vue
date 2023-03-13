<template>
<v-list>
  <template v-for="item in mainMenuItems">
    <template v-if="displayMenuItem(item)">
      <v-list-item
        v-if="!item.children"
        class="menu-item"
        :to="item.to"
        link
        :key="item.title"
        :exact="item.exact"
        >
        <v-list-item-icon v-if="item.icon">
          <v-icon>{{ item.icon }}</v-icon>
        </v-list-item-icon>
        <v-list-item-content>
          <v-list-item-title>{{ item.text }}</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
      <v-list-group v-else
                    color="white"
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
  </template>
  <settings-drawer
    :parametersList="parametersList"
    :extension="false"
    />
</v-list>
</template>

<script>
import { mapGetters } from 'vuex'
import SettingsDrawer from './SettingsDrawer.vue'

export default {
  props: ['parametersList'],
  components: {
    SettingsDrawer
  },
  computed: {
    ...mapGetters({
      authUser: 'auth/authUser'
    })
  },
  data () {
    return {
      mainMenuItems: [
        {
          text: this.$gettext('Dashboard'),
          to: { name: 'Dashboard' },
          icon: 'mdi-view-dashboard-outline',
          exact: true
        },
        {
          text: this.$gettext('Domains'),
          to: { name: 'DomainList' },
          icon: 'mdi-domain',
          roles: ['DomainAdmins', 'Resellers', 'SuperAdmins']
        },
        {
          text: this.$gettext('Identities'),
          to: { name: 'Identities' },
          icon: 'mdi-account',
          roles: ['DomainAdmins', 'Resellers', 'SuperAdmins']
        },
        {
          text: this.$gettext('Alarms'),
          to: { name: 'Alarms' },
          icon: 'mdi-bell'
        },
        {
          icon: 'mdi-history',
          text: this.$gettext('Logs'),
          roles: ['SuperAdmins', 'Resellers', 'DomainAdmins'],
          children: [
            {
              text: this.$gettext('Audit trail'),
              to: { name: 'AuditTrail' },
              roles: ['SuperAdmins']
            },
            {
              text: this.$gettext('Messages'),
              to: { name: 'MessageLog' },
              roles: ['DomainAdmins', 'Resellers', 'SuperAdmins']
            }
          ]
        },
        {
          icon: 'mdi-information',
          text: this.$gettext('Information'),
          roles: ['SuperAdmins'],
          to: { name: 'Information' }
        }
      ]
    }
  },
  methods: {
    displayMenuItem (item) {
      return (item.roles === undefined || item.roles.indexOf(this.authUser.role) !== -1) && (item.condition === undefined || item.condition())
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
