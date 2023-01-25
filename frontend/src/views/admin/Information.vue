<template>
<div>
  <v-toolbar flat>
    <v-toolbar-title><translate>Information</translate></v-toolbar-title>
  </v-toolbar>

  <components-information-table />
</div>
</template>

<script>
import ComponentsInformationTable from '@/components/admin/ComponentsInformationTable'

export default {
  components: {
    ComponentsInformationTable
  }
}
</script>
