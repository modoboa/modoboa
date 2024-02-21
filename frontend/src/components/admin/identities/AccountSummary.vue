<template>
  <v-card>
    <v-card-title>
      <span class="headline">{{ $gettext('General information') }}</span>
    </v-card-title>
    <v-card-text>
      <v-row>
        <v-col cols="6">{{ $gettext('Creation date') }}</v-col>
        <v-col cols="6">{{ $date(account.date_joined) }}</v-col>
      </v-row>
      <v-row>
        <v-col cols="6">{{ $gettext('Last login date') }}</v-col>
        <v-col v-if="account.last_login" cols="6">
          {{ $date(account.last_login) }}
        </v-col>
        <v-col v-else cols="6">{{ $gettext('Never logged-in') }}</v-col>
      </v-row>
      <v-row>
        <v-col cols="6">{{ $gettext('Full name') }}</v-col>
        <v-col cols="6">{{ account.first_name }} {{ account.last_name }}</v-col>
      </v-row>
      <v-row>
        <v-col cols="6">{{ $gettext('Role') }} </v-col>
        <v-col cols="6">{{ account.role }}</v-col>
      </v-row>
      <v-row>
        <v-col cols="6">{{ $gettext('Secondary email') }}</v-col>
        <v-col cols="6">{{ account.secondary_email }}</v-col>
      </v-row>
      <v-row>
        <v-col cols="6">{{ $gettext('Phone number') }}</v-col>
        <v-col cols="6">{{ account.phone_number }}</v-col>
      </v-row>
      <template v-if="account.mailbox">
        <v-row>
          <v-col cols="6">{{ $gettext('Quota') }} </v-col>
          <v-col v-if="account.mailbox.quota === '0'" cols="6">
            {{ $gettext('Unlimited') }}
          </v-col>
          <v-col v-else cols="6">
            <v-progress-linear
              :color="account.mailbox.quota_usage < 80 ? 'primary' : 'warning'"
              :value="account.mailbox.quota_usage"
              height="25"
              class="white--text"
            >
              <template #default="{ value }">
                {{ Math.ceil(value) }}% ({{ account.mailbox.quota }}
                {{ $gettext('MB') }})
              </template>
            </v-progress-linear>
          </v-col>
        </v-row>
        <v-row v-if="account.mailbox.message_limit">
          <v-col cols="6">{{ $gettext('Daily sending limit') }}</v-col>
          <v-col cols="6">{{ account.mailbox.message_limit }}</v-col>
        </v-row>
      </template>
    </v-card-text>
  </v-card>
</template>

<script setup lang="js">
defineProps({ account: { type: Object, default: null } })
</script>
