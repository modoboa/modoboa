<template>
  <v-card :title="$gettext('Statistics')">
    <v-card-text>
      <v-table>
        <tbody>
          <tr>
            <td>{{ $gettext('Domain count') }}</td>
            <td>{{ statistics.domain_count }}</td>
          </tr>
          <tr>
            <td>{{ $gettext('Domain alias count') }}</td>
            <td>{{ statistics.domain_alias_count }}</td>
          </tr>
          <tr>
            <td>{{ $gettext('Account count') }}</td>
            <td>{{ statistics.account_count }}</td>
          </tr>
          <tr>
            <td>{{ $gettext('Alias count') }}</td>
            <td>{{ statistics.alias_count }}</td>
          </tr>
        </tbody>
      </v-table>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'
import adminApi from '@/api/admin'

const statistics = ref({})

const response = await adminApi.getStatistics()
statistics.value = response.data
</script>
