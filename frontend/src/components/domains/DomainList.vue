<template>
  <v-layout>
    <v-flex>
      <v-toolbar flat color="white">
        <v-toolbar-title>Domains</v-toolbar-title>
        <v-divider class="mx-2" inset vertical></v-divider>
        <v-spacer></v-spacer>
        <v-text-field
            v-model="search"
            append-icon="search"
            label="Search"
            single-line
            hide-details
        ></v-text-field>
        <v-spacer></v-spacer>
        <v-btn color="primary" :to="{ name: 'DomainAdd' }">
          <v-icon>add</v-icon>
        </v-btn>
      </v-toolbar>
      <v-data-table :headers="headers" :items="domains" :search="search" class="elevation-1">
        <template slot="items" slot-scope="props">
          <td>
            <v-btn flat icon :to="{ name: 'DomainEdit', params: { domainPk: props.item.pk }}">
              <v-icon>edit</v-icon>
            </v-btn>
            <v-btn flat icon title="Remove" @click="confirmDelete(props.item)">
              <v-icon>delete</v-icon>
            </v-btn>
          </td>
          <td>
            <router-link :to="{ name: 'DomainDetail', params: { pk: props.item.pk } }">
              {{ props.item.name }}
            </router-link>
          </td>
          <td>
            <v-chip v-if="props.item.dns_status.checks === 'disabled'"
                    text-color="white" small>Disabled</v-chip>
            <v-chip v-if="props.item.dns_status.checks === 'pending'"
                    color="secondary" text-color="white" small>Pending</v-chip>
            <span v-if="props.item.dns_status.checks === 'active'">
              <v-chip v-if="props.item.dns_status.mx"
                      :color="getDNSTagType(props.item.dns_status.mx)"
                      text-color="white" small
              >
                MX
              </v-chip>
              <v-chip v-if="props.item.dns_status.dnsbl"
                      :color="getDNSTagType(props.item.dns_status.dnsbl)"
                      text-color="white" small
              >
                DNSBL
              </v-chip>
            </span>
          </td>
          <td>
            <v-progress-linear v-model="props.item.allocated_quota_in_percent"></v-progress-linear>
          </td>
        </template>
      </v-data-table>
    </v-flex>
  </v-layout>
  <!-- <div>
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
       </div> -->
</template>

<script>
import { mapGetters } from 'vuex'

export default {
    computed: mapGetters(['domains']),
    data () {
        return {
            headers: [
                { text: '', value: 'name' },
                { text: 'Name', value: 'name' },
                { text: 'DNS status', value: 'dns_status' },
                { text: 'Quota', value: 'allocated_quota_in_percent' }
            ],
            search: ''
        }
    },
    created () {
        this.$store.dispatch('getDomains')
    },
    methods: {
        confirmDelete (domain) {
            this.$dialog.prompt({
                message: `Delete domain ${domain.name}?`,
                inputAttrs: {
                    type: 'checkbox',
                    placeholder: 'Keep mailboxes on filesystem'
                },
                onConfirm: value => this.$toast.open(`Your age is: ${value}`)
            })
        },
        getDNSTagType (value) {
            if (value === 'unknown') {
                return 'orange'
            } else if (value === 'ok') {
                return 'red'
            } else {
                return 'green'
            }
        }
    }
}
</script>
