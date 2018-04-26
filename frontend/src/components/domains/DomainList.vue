<template>
  <div>
    <div class="columns">
      <div class="column">
        <h1 class="title">Domains</h1>
      </div>
      <div class="column">
        <router-link :to="{ name: 'DomainAdd' }" class="button is-primary">Add</router-link>
        <b-dropdown>
          <button class="button" slot="trigger">
            <span>Actions</span>
            <b-icon icon="menu-down"></b-icon>
          </button>
          <b-dropdown-item>Import</b-dropdown-item>
          <b-dropdown-item>Export</b-dropdown-item>
        </b-dropdown>
      </div>
      <div class="column">
        <b-field>
          <b-input placeholder="Search..." type="search" icon="magnify"></b-input>
        </b-field>
      </div>
    </div>
    <b-table :data="domains" paginated checkable>
      <template slot-scope="props">
        <b-table-column :sortable="false">
          <router-link :to="{ name: 'DomainEdit', params: { domainPk: props.row.pk }}">
            <b-icon icon="pencil"></b-icon>
          </router-link>
          <a href="#" title="Remove"  @click="confirmDelete(props.row)">
            <b-icon icon="delete"></b-icon>
          </a>
        </b-table-column>
        <b-table-column sortable field="name" label="Name">
          {{ props.row.name }}
        </b-table-column>
        <b-table-column field="dns_status" label="DNS status">
          <b-tag v-if="props.row.dns_status.checks === 'disabled'" rounded>Disabled</b-tag>
          <b-tag v-if="props.row.dns_status.checks === 'pending'" type="is-info" rounded>Pending</b-tag>
          <b-taglist v-if="props.row.dns_status.checks === 'active'">
            <b-tag v-if="props.row.dns_status.mx" :type="getDNSTagType(props.row.dns_status.mx)" rounded>MX</b-tag>
            <b-tag v-if="props.row.dns_status.dnsbl" :type="getDNSTagType(props.row.dns_status.dnsbl)" rounded>DNSBL</b-tag>
          </b-taglist>
        </b-table-column>
        <b-table-column field="quota" label="Quota">
          <progress class="progress is-primary"
                    :value="props.row.allocated_quota_in_percent" max="100">
            {{ props.row.allocated_quota_in_percent }}%
          </progress>
        </b-table-column>
      </template>
    </b-table>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  computed: mapGetters(['domains']),
  data() {
    return {}
  },
  created() {
    this.$store.dispatch('getDomains')
  },
  methods: {
    confirmDelete(domain) {
      this.$dialog.prompt({
        message: `Delete domain ${domain.name}?`,
        inputAttrs: {
          type: 'checkbox',
          placeholder: 'Keep mailboxes on filesystem'
        },
        onConfirm: value => this.$toast.open(`Your age is: ${value}`)
      })
    },
    getDNSTagType(value) {
      if (value === 'unknown') {
        return 'is-warning'
      } else if (value === 'ok') {
        return 'is-danger'
      } else {
        return 'is-success'
      }
    }
  }
}
</script>
