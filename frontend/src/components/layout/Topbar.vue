<template>
<v-app-bar
  color="primary"
  dark
  app
  clipped-left
  >
  <div class="d-flex justify-start">
    <v-img
      class="mx-2"
      src="../../assets/Modoboa_RVB-BLANC-SANS.png"
      contain
      width="200"
      />
  </div>
  <v-spacer />
  <v-menu rounded="lg" offset-y>
    <template v-slot:activator="{ attrs, on }">
      <v-btn
        color="white"
        v-bind="attrs"
        v-on="on"
        icon
        >
        <v-icon>mdi-account-outline</v-icon>
      </v-btn>
    </template>
    <v-list>
      <v-list-item
        v-for="item in items"
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
</v-app-bar>
</template>

<script>
export default {
  data () {
    return {
      items: [
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
        this.$router.push('/login')
      })
    }
  }
}
</script>
