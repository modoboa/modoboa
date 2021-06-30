<template>
<div>
  <v-toolbar flat>
    <v-toolbar-title><translate>Welcome to Modoboa</translate></v-toolbar-title>
  </v-toolbar>
  <v-alert
    type="info"
    border="top"
    colored-border
    elevation="2"
    class="mt-10"
    >
    <translate tag="p">This page is still under construction.</translate>
    <translate tag="p">
      It will present a summary of your Modoboa server's status and
      some useful information about the product.
    </translate>
    <p>
      Your feedback would be really appreciated, you can
      use <a href="https://github.com/modoboa/modoboa/discussions">Github
      discussions</a> to share your ideas and/or comments.
    </p>
  </v-alert>
</div>
</template>
