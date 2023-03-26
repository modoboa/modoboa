<template>
<v-card class="mt-6">
  <v-toolbar flat>
    <v-menu offset-y>
      <template v-slot:activator="{ on, attrs }">
        <v-btn v-bind="attrs" v-on="on" small>
          Actions <v-icon right>mdi-chevron-down</v-icon>
        </v-btn>
      </template>
      <v-list dense>
        <menu-items :items="getActionMenuItems()"/>
      </v-list>
    </v-menu>
    <v-spacer></v-spacer>
    <v-text-field
      v-model="search"
      prepend-inner-icon="mdi-magnify"
      placeholder="Search"
      filled
      outlined
      dense
      hide-details
      ></v-text-field>
  </v-toolbar>
  <v-data-table
    v-model="selected"
    :headers="headers"
    :items="alarms"
    :search="search"
    item-key="id"
    :options.sync="options"
    :server-items-length="totalAlarms"
    :loading="loading"
    class="elevation-1"
    show-select
    >
    <template v-slot:item.status="{ item }">
      <v-chip
        v-if="item.status === 1"
        color="warning"
        small
        >
        <translate>Opened</translate>
      </v-chip>
      <v-chip
        v-else
        color="info"
        small
        >
        <translate>Closed</translate>
      </v-chip>
    </template>
    <template v-slot:item.mailbox="{ item }">
      <template v-if="item.mailbox">
        {{ item.mailbox.address }}@{{ item.domain.name }}
      </template>
      <template v-else>
        /
      </template>
    </template>
    <template v-slot:item.created="{ item }">
      {{ item.created|date }}
    </template>
    <template v-slot:item.actions="{ item }">
      <div class="text-right">
        <v-menu offset-y>
          <template v-slot:activator="{ on, attrs }">
            <v-btn icon v-bind="attrs" v-on="on">
              <v-icon>mdi-dots-horizontal</v-icon>
            </v-btn>
          </template>
          <menu-items :items="getMenuItems(item)" :object="item" />
        </v-menu>
      </div>
    </template>
  </v-data-table>
</v-card>
</template>

<script>
import { bus } from '@/main'
import alarms from '@/api/alarms'
import debounce from 'debounce'
import MenuItems from '@/components/tools/MenuItems'
import constants from '@/constants.json'

export default {
  components: {
    MenuItems
  },
  data () {
    return {
      alarms: [],
      headers: [
        { text: this.$gettext('Triggered'), value: 'created' },
        { text: this.$gettext('Status'), value: 'status' },
        { text: this.$gettext('Domain'), value: 'domain.name', sortable: false },
        { text: this.$gettext('Mailbox'), value: 'mailbox', sortable: false },
        { text: this.$gettext('Message'), value: 'title' },
        { text: this.$gettext('Actions'), value: 'actions', sortable: false, align: 'right' }
      ],
      loading: true,
      options: {},
      search: '',
      selected: [],
      totalAlarms: 0
    }
  },
  methods: {
    fetchAlarms () {
      const params = {
        page: this.options.page
      }
      if (this.options.sortBy) {
        params.ordering = this.options.sortBy.map(item => this.options.sortDesc[0] ? `-${item}` : item).join(',')
      }
      if (this.search !== '') {
        params.search = this.search
      }
      this.loading = true
      alarms.getAll(params).then(resp => {
        this.alarms = resp.data.results
        this.totalAlarms = resp.data.count
        this.loading = false
      })
    },
    async deleteAlarm (alarm, single = true) {
      alarms.delete(alarm.id).then(() => {
        if (single) {
          bus.$emit('notification', { msg: this.$gettext('Alarm deleted') })
          this.fetchAlarms()
        }
      })
    },
    async closeAlarm (alarm) {
      alarms.switchStatus(alarm.id, { status: constants.ALARM_CLOSED }).then(() => {
        bus.$emit('notification', { msg: this.$gettext('Alarm closed') })
        this.fetchAlarms()
      })
    },
    async openAlarm (alarm) {
      alarms.switchStatus(alarm.id, { status: constants.ALARM_OPENED }).then(() => {
        bus.$emit('notification', { msg: this.$gettext('Alarm re-opened') })
        this.fetchAlarms()
      })
    },
    async deleteAlarms () {
      await alarms.bulkDelete(this.selected.map(alarm => alarm.id))
      bus.$emit('notification', { msg: this.$gettext('Alarms deleted') })
      this.selected = []
      this.fetchAlarms()
    },
    getMenuItems (item) {
      const result = []
      result.push({
        label: this.$gettext('Delete'),
        icon: 'mdi-delete-outline',
        onClick: this.deleteAlarm,
        color: 'red'
      })
      if (item.status === constants.ALARM_OPENED) {
        result.push({
          label: this.$gettext('Close alarm'),
          icon: 'mdi-check',
          onClick: this.closeAlarm,
          color: 'green'
        })
      } else {
        result.push({
          label: this.$gettext('Reopen alarm'),
          icon: 'mdi-alert-circle-outline',
          onClick:
          this.openAlarm,
          color: 'orange'
        })
      }
      return result
    },
    getActionMenuItems () {
      const result = []
      if (this.selected.length > 0) {
        result.push({ label: this.$gettext('Delete'), icon: 'mdi-delete-outline', onClick: this.deleteAlarms, color: 'red' })
      }
      result.push({ label: this.$gettext('Reload'), icon: 'mdi-reload', onClick: this.fetchAlarms })
      return result
    }
  },
  mounted () {
    this.fetchAlarms()
  },
  created () {
    this.fetchAlarms = debounce(this.fetchAlarms, 500)
  },
  watch: {
    options: {
      handler () {
        this.fetchAlarms()
      },
      deep: true
    },
    search () {
      this.fetchAlarms()
    }
  }
}
</script>
