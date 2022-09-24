<template>
<v-navigation-drawer
    v-model="drawer"
    :mini-variant.sync="mini"
    permanent
    :color="mainColor"
    app
    dark
    >
    <div class="d-flex align-center">
      <v-img
        src="../../assets/Modoboa_RVB-BLANC-SANS.png"
        max-width="190"
        class="logo"
        @click="$router.push('/')"
        />
      <v-btn
        icon
        @click.stop="mini = !mini"
        >
        <v-icon>mdi-chevron-left</v-icon>
      </v-btn>
    </div>

    <v-list>
      <template v-for="item in menuItems">
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
    </v-list>
    <template v-slot:append>
      <v-menu rounded="lg" offset-y top>
        <template v-slot:activator="{ attrs, on }">
          <div class="d-flex user-box justify-center align-center white--text py-2" v-bind="attrs" v-on="on">
            <v-avatar size="40" color="primary">
              <span class="white--text headline">{{ userInitials }}</span>
            </v-avatar>
            <template v-if="!mini">
              <span class="mx-2">{{ displayName }}</span>
              <v-icon class="float-right">mdi-chevron-up</v-icon>
            </template>
          </div>
        </template>
        <v-list>
          <v-list-item
            v-for="item in userMenuItems"
            :key="item.text"
            :to="item.to"
            @click="item.click"
            link
            >
            <v-list-item-icon v-if="item.icon">
              <v-icon>{{ item.icon }}</v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>{{ item.text }}</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </v-list>
      </v-menu>
    </template>
  </v-navigation-drawer>
</template>

<script>
import parameters from '@/api/parameters'
import { mapGetters } from 'vuex'

export default {
  computed: {
    ...mapGetters({
      authUser: 'auth/authUser'
    }),
    userInitials () {
      let initials = null
      if (this.authUser.first_name) {
        initials = this.authUser.first_name[0]
      }
      if (this.authUser.last_name) {
        initials = initials ? initials + this.authUser.last_name[0] : this.authUser.last_name[0]
      }
      if (!initials) {
        initials = this.authUser.username[0]
      }
      return initials
    },
    displayName () {
      return (this.authUser.first_name || this.authUser.last_name)
        ? `${this.authUser.first_name} ${this.authUser.last_name}`
        : this.authUser.username
    },
    menuItems () {
      if (this.$route.meta.layout === 'user') {
        return this.userSettingsMenuItems
      }
      return this.mainMenuItems
    },
    mainColor () {
      if (this.$route.meta.layout === 'user') {
        return 'grey'
      }
      return 'primary'
    }
  },
  data () {
    return {
      drawer: true,
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
          icon: 'mdi-cog',
          text: this.$gettext('Settings'),
          children: [],
          roles: ['SuperAdmins']
        }
      ],
      userSettingsMenuItems: [
        {
          text: this.$gettext('Profile'),
          to: { name: 'UserProfile' },
          icon: 'mdi-account-circle-outline',
          exact: true
        },
        {
          text: this.$gettext('Security'),
          to: { name: 'UserSecurity' },
          icon: 'mdi-lock-outline',
          exact: true
        },
        // {
        //   text: this.$gettext('Preferences'),
        //   icon: 'mdi-tune',
        //   exact: true
        // },
        {
          text: this.$gettext('Forward'),
          condition: () => this.authUser.mailbox !== null,
          to: { name: 'UserForward' },
          icon: 'mdi-forward',
          exact: true
        }
      ],
      mini: false,
      userMenuItems: [
        {
          text: this.$gettext('Profile'),
          icon: 'mdi-account-circle-outline',
          to: { name: 'UserProfile' },
          click: () => null
        },
        {
          text: this.$gettext('Logout'),
          icon: 'mdi-logout',
          click: this.logout
        }
      ]
    }
  },
  created () {
    parameters.getApplications().then(response => {
      response.data.forEach(item => {
        this.mainMenuItems[5].children.push({
          text: item.label,
          to: { name: 'ParametersEdit', params: { app: item.name } }
        })
      })
    })
  },
  methods: {
    displayMenuItem (item) {
      return (item.roles === undefined || item.roles.indexOf(this.authUser.role) !== -1) && (item.condition === undefined || item.condition())
    },
    logout () {
      this.$store.dispatch('auth/logout').then(() => {
        this.$router.push({ name: 'Login' })
      })
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

.user-box {
  background: rgba(0, 0, 0, 0.25);
}

.logo {
  cursor: pointer;
}
</style>
