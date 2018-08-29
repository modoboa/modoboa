<template>
  <v-app>
    <navbar ref="navbar"></navbar>
    <v-toolbar
        :clipped-left="$vuetify.breakpoint.lgAndUp"
        color="blue darken-3"
        dark
        app
    >
      <v-toolbar-title style="width: 300px" class="ml-0 pl-3">
        <v-toolbar-side-icon @click.stop="$refs.navbar.drawer = !$refs.navbar.drawer">
        </v-toolbar-side-icon>
        <span class="hidden-sm-and-down">Modoboa</span>
      </v-toolbar-title>
    </v-toolbar>
    <v-content>
      <v-container fluid>
        <router-view/>
      </v-container>
    </v-content>
  </v-app>
</template>

<script>
import Navbar from './components/navigation/Navbar'

export default {
    name: 'App',
    components: { Navbar }
}
</script>
