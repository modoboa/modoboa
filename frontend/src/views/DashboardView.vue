<template>
  <v-toolbar flat>
    <v-toolbar-title>{{ $gettext('Welcome to Modoboa') }}</v-toolbar-title>
  </v-toolbar>
  <v-alert type="info" border="top" colored-border elevation="2" class="mt-10">
    <p>{{ $gettext('This page is still under construction.') }}</p>
    <p>
      {{
        $gettext(
          "It will present a summary of your Modoboa server's status and some useful information about the product."
        )
      }}
    </p>
    <p>
      Your feedback would be really appreciated, you can use
      <a href="https://github.com/modoboa/modoboa/discussions"
        >Github discussions</a
      >
      to share your ideas and/or comments.
    </p>
  </v-alert>
</template>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}

.v-tabs-items {
  background-color: #f7f8fa !important;
}
</style>
