<template>
<div>
  <v-toolbar flat>
    <v-toolbar-title><translate>Alias</translate> {{ alias.address }}</v-toolbar-title>
    <v-btn color="primary" icon :to="{ name: 'AliasEdit', params: { id: alias.pk } }">
      <v-icon>mdi-circle-edit-outline</v-icon>
    </v-btn>
  </v-toolbar>
  <v-row>
    <v-col cols="6">
      <alias-summary :alias="alias" />
      <alias-recipients :alias="alias" class="mt-2" />
    </v-col>
  </v-row>
</div>
</template>

<script>
import aliases from '@/api/aliases'
import AliasRecipients from '@/components/identities/AliasRecipients'
import AliasSummary from '@/components/identities/AliasSummary'

export default {
  components: {
    AliasRecipients,
    AliasSummary
  },
  data () {
    return {
      alias: { pk: this.$route.params.id }
    }
  },
  mounted () {
    aliases.get(this.$route.params.id).then(resp => {
      this.alias = resp.data
    })
  }
}
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
