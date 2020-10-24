<template>
<div>
  <v-tabs v-model="tab">
    <v-tab>Domains</v-tab>
    <v-tab>Aliases</v-tab>
  </v-tabs>
  <v-tabs-items v-model="tab">
    <v-tab-item>
      <domain-list />
    </v-tab-item>
    <v-tab-item>
      <domain-alias-list />
    </v-tab-item>
  </v-tabs-items>
</div>
</template>

<script>
import DomainList from '@/components/domains/DomainList'
import DomainAliasList from '@/components/domains/DomainAliasList'

export default {
  components: {
    DomainList,
    DomainAliasList
  },
  data () {
    return {
      tab: null
    }
  }
}
</script>
