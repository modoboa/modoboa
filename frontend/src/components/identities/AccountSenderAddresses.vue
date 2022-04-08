<template>
<v-card>
  <v-card-title>
    <translate class="headline">Sender addresses</translate>
  </v-card-title>
  <v-card-text>
    <v-data-table
      :headers="headers"
      :items="addresses"
      hide-default-footer
      :no-data-text="'No sender address defined for this account'|translate"
      >
      <template v-slot:item.address="{ item }">
        <span v-if="item.pk">{{ item.address }}</span>
        <v-text-field
          v-else
          v-model="newAddress"
          :label="'Specify an email address'|translate"
          >
          <template v-slot:append-outer>
            <v-btn v-if="newAddress" icon color="primary" @click="submit">
              <v-icon>mdi-content-save</v-icon>
            </v-btn>
          </template>
        </v-text-field>
      </template>
      <template v-slot:item.actions="{ item }">
        <v-btn v-if="item.pk"
               icon
               color="red"
               @click="deleteSenderAddress(item)"
               :title="'Remove this address'|translate"
               >
          <v-icon>mdi-delete-outline</v-icon>
        </v-btn>
      </template>
    </v-data-table>
    <v-btn
      v-if="!hideAddBtn"
      small
      color="primary"
      outlined
      @click="addRow"
      >
      <v-icon small>mdi-plus</v-icon> <translate>Add sender address</translate>
    </v-btn>
  </v-card-text>
</v-card>
</template>

<script>
import { bus } from '@/main'
import senderAddresses from '@/api/senderAddresses'

export default {
  props: {
    account: Object
  },
  data () {
    return {
      addresses: [],
      headers: [
        { text: this.$gettext('Address'), value: 'address' },
        { text: '', value: 'actions', align: 'right', sortable: false }
      ],
      hideAddBtn: false,
      newAddress: null
    }
  },
  methods: {
    addRow () {
      this.addresses.push({})
      this.hideAddBtn = true
    },
    fetchSenderAddresses () {
      senderAddresses.getAllForMailbox(this.account.mailbox.pk).then(resp => {
        this.addresses = resp.data
      })
    },
    submit () {
      const data = {
        address: this.newAddress,
        mailbox: this.account.mailbox.pk
      }
      senderAddresses.create(data).then(response => {
        this.fetchSenderAddresses()
        this.newAddress = null
        this.hideAddBtn = false
        bus.$emit('notification', { msg: this.$gettext('Sender address added') })
      })
    },
    deleteSenderAddress (senderAddress) {
      senderAddresses.delete(senderAddress.pk).then(response => {
        this.fetchSenderAddresses()
        bus.$emit('notification', { msg: this.$gettext('Sender address deleted') })
      })
    }
  },
  mounted () {
    this.fetchSenderAddresses()
  }
}
</script>
