<template>
  <v-row>
    <v-col v-for="tile in tiles" :key="tile.key" cols="6" md="3">
      <v-card :to="tile.to" height="100%">
        <v-card-text class="d-flex align-center">
          <v-icon
            :icon="tile.icon"
            size="x-large"
            color="primary"
            class="mr-4"
          />
          <div>
            <div class="text-h4">{{ statistics[tile.key] }}</div>
            <div class="text-medium-emphasis">{{ tile.label }}</div>
          </div>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>

<script setup>
import { ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import adminApi from '@/api/admin'

const { $gettext } = useGettext()

const statistics = ref({})

const tiles = [
  {
    key: 'domain_count',
    label: $gettext('Domains'),
    icon: 'mdi-domain',
    to: { name: 'DomainList' },
  },
  {
    key: 'domain_alias_count',
    label: $gettext('Domain aliases'),
    icon: 'mdi-link-variant',
    to: { name: 'DomainList' },
  },
  {
    key: 'account_count',
    label: $gettext('Accounts'),
    icon: 'mdi-account-multiple',
    to: { name: 'Identities' },
  },
  {
    key: 'alias_count',
    label: $gettext('Aliases'),
    icon: 'mdi-at',
    to: { name: 'Identities' },
  },
]

const response = await adminApi.getStatistics()
statistics.value = response.data
</script>
