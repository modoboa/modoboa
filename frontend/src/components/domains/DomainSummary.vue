<template>
<v-card v-if="domain">
  <v-card-title>
    <translate class="headline">General information</translate>
  </v-card-title>
  <v-card-text>
    <v-row>
      <v-col cols="6"><translate>Creation date</translate></v-col>
      <v-col cols="6">{{ domain.creation|date }}</v-col>
    </v-row>
    <v-row>
      <v-col cols="6"><translate>Last modification date</translate></v-col>
      <v-col cols="6">{{ domain.last_modification|date }}</v-col>
    </v-row>
    <v-row>
      <v-col cols="6"><translate>Quota</translate></v-col>
      <v-col cols="6" v-if="domain.quota === '0'"><translate>Unlimited</translate></v-col>
      <v-col cols="6" v-else>{{ domain.quota }} <translate>MB</translate></v-col>
    </v-row>
    <v-row>
      <v-col cols="6"><translate>Default mailbox quota</translate></v-col>
      <v-col cols="6" v-if="domain.default_mailbox_quota === '0'"><translate>Unlimited</translate></v-col>
      <v-col cols="6" v-else>{{ domain.default_mailbox_quota }} MB</v-col>
    </v-row>
    <v-row v-if="domain.message_limit !== undefined">
      <v-col cols="6"><translate>Daily sending limit</translate></v-col>
      <v-col cols="6">{{ domain.message_limit }} <translate>messages</translate></v-col>
    </v-row>
    <v-row>
      <v-col cols="6"><translate>Mailboxes</translate></v-col>
      <v-col cols="6">{{ domain.mailbox_count }}</v-col>
    </v-row>
    <v-row>
      <v-col cols="6"><translate>Aliases</translate></v-col>
      <v-col cols="6">{{ domain.mbalias_count }}</v-col>
    </v-row>
  </v-card-text>
</v-card>
</template>

<script>
export default {
  props: ['domain']
}
</script>
