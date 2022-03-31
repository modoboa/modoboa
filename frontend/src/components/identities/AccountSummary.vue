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
