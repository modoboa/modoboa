<template>
<div>
  <v-toolbar flat>
    <v-toolbar-title><translate>Domains</translate></v-toolbar-title>
    <v-spacer />
    <v-btn class="mr-2">
      <v-icon>mdi-file-import-outline</v-icon>
    </v-btn>
    <v-btn class="mr-2">
      <v-icon>mdi-file-export-outline</v-icon>
    </v-btn>
    <v-btn color="primary" :to="{ name: 'DomainAdd' }">
      <v-icon>mdi-plus</v-icon>
    </v-btn>
  </v-toolbar>
  <domain-list />
</div>
</template>

<script>
import DomainList from '@/components/domains/DomainList'

export default {
  components: {
    DomainList
  },
  data () {
    return {
    }
  }
}
</script>
