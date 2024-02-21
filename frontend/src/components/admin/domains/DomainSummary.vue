<template>
  <v-card v-if="domain">
    <v-card-title>
      <div class="headline">{{ $gettext('General information') }}</div>
    </v-card-title>
    <v-card-text>
      <v-row>
        <v-col cols="6">{{ $gettext('Creation date') }}</v-col>
        <v-col cols="6">{{ $date(domain.creation) }}</v-col>
      </v-row>
      <v-row>
        <v-col cols="6">{{ $gettext('Last modification date') }}</v-col>
        <v-col cols="6">{{ $date(domain.last_modification) }}</v-col>
      </v-row>
      <v-row>
        <v-col cols="6">{{ $gettext('Quota') }}</v-col>
        <v-col v-if="domain.quota === '0'" cols="6">{{
          $gettext('Unlimited')
        }}</v-col>
        <v-col v-else cols="6">{{ domain.quota }} {{ $gettext('MB') }}</v-col>
      </v-row>
      <v-row>
        <v-col cols="6">{{ $gettext('Default mailbox quota') }}</v-col>
        <v-col v-if="domain.default_mailbox_quota === '0'" cols="6">{{
          $gettext('Unlimited')
        }}</v-col>
        <v-col v-else cols="6">{{ domain.default_mailbox_quota }} MB</v-col>
      </v-row>
      <v-row v-if="domain.message_limit !== undefined">
        <v-col cols="6">{{ $gettext('Daily sending limit') }}</v-col>
        <v-col cols="6"
          >{{ domain.message_limit }} {{ $gettext('messages') }}</v-col
        >
      </v-row>
      <v-row>
        <v-col cols="6">{{ $gettext('Mailboxes') }}</v-col>
        <v-col cols="6">{{ domain.mailbox_count }}</v-col>
      </v-row>
      <v-row>
        <v-col cols="6">{{ $gettext('Aliases') }}</v-col>
        <v-col cols="6">{{ domain.mbalias_count }}</v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup lang="js">
import { useGettext } from 'vue3-gettext'

const { $gettext } = useGettext()
defineProps({ domain: { type: Object, default: null } })
</script>
