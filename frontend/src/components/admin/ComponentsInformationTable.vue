<template>
<v-card class="mt-6">
  <v-card-title>
    <translate>Installed components</translate>
  </v-card-title>
  <v-card-text>
    <v-alert
      outlined
      type="success"
      text
      border="left"
      v-if="updatesAvailable"
      >
      <translate tag="p">One or more updates are available</translate>
      <translate tag="p" class="text-body-2">
        Check out the following list to find related components
      </translate>
    </v-alert>
    <v-data-table
      :headers="headers"
      :items="components"
      :item-class="getItemBackground"
      hide-default-footer
      >
      <template v-slot:item.last_version="{ item }">
        <template v-if="item.changelog_url">
          <a :href="item.changelog_url" target="_blank">{{ item.last_version }}</a>
        </template>
        <template v-else>
          {{ item.last_version }}
        </template>
      </template>
    </v-data-table>
  </v-card-text>
</v-card>
</template>

<script>
import adminApi from '@/api/admin'

export default {
  computed: {
    updatesAvailable () {
      return this.components.filter(item => item.update).length > 0
    }
  },
  data () {
    return {
      components: [],
      headers: [
        { text: this.$gettext('Name'), value: 'name' },
        { text: this.$gettext('Installed version'), value: 'version' },
        { text: this.$gettext('Latest version'), value: 'last_version' },
        { text: this.$gettext('Description'), value: 'description' }
      ]
    }
  },
  methods: {
    getItemBackground (item) {
      if (item.update) {
        return 'green lighten-5'
      }
      return ''
    }
  },
  mounted () {
    adminApi.getComponentsInformation().then(resp => {
      this.components = resp.data
    })
  }
}
</script>
