<template>
<v-list>
  <template v-for="item in extensionItems">
    <template v-if="!(item.activated)">
      <v-list-item
        class="menu-item unselectable"
        :key="item.title"
        :exact="item.exact"
        color="blue-grey lighten-3"
        @click="unselectable()"
        >
       <v-list-item-icon v-if="item.icon">
          <v-icon color="#D3D3D3">{{ item.icon }}</v-icon>
        </v-list-item-icon>
        <v-list-item-content>
          <v-list-item-title>{{ item.text }}</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
    </template>
    <template v-else-if="displayMenuItem(item)">
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
    :extension="true"
    />
</v-list>
</template>

<script>
import { mapGetters } from 'vuex'
import { bus } from '@/main'
import SettingsDrawer from './SettingsDrawer.vue'

export default {
  props: ['imap', 'parametersList'],
  components: {
    SettingsDrawer
  },
  computed: {
    ...mapGetters({
      authUser: 'auth/authUser'
    }),
    extensionItems () {
      return [
        {
          activated: this.imapMigration,
          icon: 'mdi-email-sync-outline',
          text: this.$gettext('IMAP Migration'),
          roles: ['SuperAdmins', 'Resellers'],
          children: [
            {
              text: this.$gettext('Email providers'),
              to: { name: 'ProvdiersList' },
              roles: ['SuperAdmins', 'Resellers']
            },
            {
              text: this.$gettext('Migrations'),
              to: { name: 'MigrationsList' },
              roles: ['Resellers', 'SuperAdmins']
            }
          ]
        }
      ]
    }
  },
  created () {
    this.imapMigration = this.imap
    bus.$on('imapSettingsChanged', this.imapMigrationStatus)
  },
  data () {
    return {
      imapMigration: false
    }
  },
  methods: {
    displayMenuItem (item) {
      return (item.roles === undefined || item.roles.indexOf(this.authUser.role) !== -1) && (item.condition === undefined || item.condition())
    },
    unselectable () {
      bus.$emit('notification', { msg: this.$gettext('Activate the extension in the settings'), type: 'warning' })
    },
    imapMigrationStatus (status) {
      this.imapMigration = status
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
.unselectable {
  color: lightgrey !important;
}
</style>
