<template>
  <v-navigation-drawer
    v-model="drawer"
    color="primary"
    app
    dark
    >
    <div class="d-flex justify-center">
      <v-img
        src="../../assets/Modoboa_RVB-BLANC-SANS.png"
        max-width="190"
        />
    </div>

    <v-list>
      <template v-for="item in mainMenuItems">
        <v-list-item
          v-if="!item.children"
          class="menu-item"
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
    </v-list>
    <template v-slot:append>
      <v-menu rounded="lg" offset-y top>
        <template v-slot:activator="{ attrs, on }">
          <div class="user-box justify-end white--text" v-bind="attrs" v-on="on">
            <v-avatar size="40" color="primary">
              <span class="white--text headline">AN</span>
            </v-avatar>
            <span class="mx-2">{{ authUser.first_name }} {{ authUser.last_name }}</span>
            <v-icon class="float-right">mdi-chevron-up</v-icon>
          </div>
        </template>
        <v-list>
          <v-list-item
            v-for="item in userMenuItems"
            :key="item.text"
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
    })
  },
  data () {
    return {
      drawer: true,
      mainMenuItems: [
        {
          text: this.$gettext('Dashboard'),
          icon: 'mdi-view-dashboard-outline'
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
          icon: 'mdi-history',
          text: this.$gettext('Logs'),
          to: { name: 'LogList' }
        },
        {
          icon: 'mdi-cog',
          text: this.$gettext('Parameters'),
          children: []
        }
      ],
      userMenuItems: [
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
        this.mainMenuItems[4].children.push({
          text: item.label,
          to: { name: 'ParametersEdit', params: { app: item.name } }
        })
      })
    })
  },
  methods: {
    logout () {
      this.$store.dispatch('auth/logout').then(() => {
        this.$router.push('/login')
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.v-list-item {
  &--active {
    &::before {
      background-color: #000;
      opacity: 0.3;
    }
  }
}

.user-box {
  box-sizing: border-box;
  border: 1px solid #979797;
  width: 100%;
  background: rgba(0, 0, 0, 0.25);
  padding: 5px;
}
</style>
