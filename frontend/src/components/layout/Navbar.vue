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
    <v-layout
      justify-center>
      <v-chip v-if="page === 1" color="blue lighten-3" large>
        <translate>Core</translate>
      </v-chip>
      <v-chip v-else-if="page === 2" color="blue lighten-3" large>
        <translate>Extensions</translate>
      </v-chip>
    </v-layout>
    <base-nav-bar
      v-if="page === 1"
      :parametersList="parametersList"
      />
    <extension-nav-bar
      v-else-if="page === 2"
      :imap="imapMigration"
      :parametersList="parametersList"
      />
    <template v-slot:append>
      <v-pagination
        v-if="!mini"
        v-model="page"
        :length="2"
        circle
        color="blue lighten-3"
        >
      </v-pagination>
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
import { mapGetters } from 'vuex'
import BaseNavBar from './BaseNavBar.vue'
import ExtensionNavBar from './ExtensionNavBar.vue'
import parameters from '@/api/parameters'

export default {
  components: {
    BaseNavBar,
    ExtensionNavBar
  },
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
    mainColor () {
      if (this.$route.meta.layout === 'user') {
        return 'grey'
      }
      return 'primary'
    }
  },
  created () {
    parameters.getApplications().then(response => {
      this.parametersList = response.data
    })
    parameters.getApplication('imap_migration').then(response => {
      this.imapMigration = response.data.params.enabled_imapmigration
    })
  },
  data () {
    return {
      parametersList: [],
      imapMigration: false,
      page: 1,
      drawer: true,
      userSettingsMenuItems: [
        {
          text: this.$gettext('API'),
          roles: ['SuperAdmins'],
          to: { name: 'APISetup' },
          icon: 'mdi-api',
          exact: true
        },
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
  methods: {
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
