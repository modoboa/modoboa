<template>
<v-card>
  <v-card-title>
    <translate class="headline">General information</translate>
  </v-card-title>
  <v-card-text>
    <v-row>
      <v-col cols="6"><translate>Creation date</translate></v-col>
      <v-col cols="6">{{ account.date_joined|date }}</v-col>
    </v-row>
    <v-row>
      <v-col cols="6"><translate>Last login date</translate></v-col>
      <v-col v-if="account.last_login" cols="6">{{ account.last_login|date }}</v-col>
      <v-col v-else cols="6"><translate>Never logged-in</translate></v-col>
    </v-row>
    <v-row>
      <v-col cols="6"><translate>Full name</translate></v-col>
      <v-col cols="6">{{ account.first_name }} {{ account.last_name }}</v-col>
    </v-row>
    <v-row>
      <v-col cols="6"><translate>Role</translate></v-col>
      <v-col cols="6">{{ account.role }}</v-col>
    </v-row>
    <v-row>
      <v-col cols="6"><translate>Secondary email</translate></v-col>
      <v-col cols="6">{{ account.secondary_email }}</v-col>
    </v-row>
    <v-row>
      <v-col cols="6"><translate>Phone number</translate></v-col>
      <v-col cols="6">{{ account.phone_number }}</v-col>
    </v-row>
    <template v-if="account.mailbox">
      <v-row>
        <v-col cols="6"><translate>Quota</translate></v-col>
        <v-col cols="6">
          <v-progress-linear
            :color="account.mailbox.quota_usage < 80 ? 'primary' : 'warning'"
            :value="account.mailbox.quota_usage"
            height="25"
            class="white--text"
            >
            <template v-slot:default="{ value }">
              {{ Math.ceil(value) }}% ({{ account.mailbox.quota }} <translate>MB</translate>)
            </template>
          </v-progress-linear>
        </v-col>
      </v-row>
      <v-row v-if="account.mailbox.message_limit">
        <v-col cols="6"><translate>Daily sending limit</translate></v-col>
        <v-col cols="6">{{ account.mailbox.message_limit }}</v-col>
      </v-row>

    </template>
  </v-card-text>
</v-card>
</template>

<script>
export default {
  props: {
    account: Object
  }
}
</script>
