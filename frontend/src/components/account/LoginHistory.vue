<template>
  <v-card flat>
    <v-card-text>
      <p class="mb-4">
        {{
          $gettext(
            'The latest sign-ins and failed attempts on your account. If you do not recognize one of them, change your password.'
          )
        }}
      </p>
      <v-data-table
        :headers="headers"
        :items="logins"
        :loading="loading"
        :no-data-text="$gettext('No login recorded yet')"
        mobile-breakpoint="sm"
        hide-default-footer
        items-per-page="-1"
      >
        <template #[`item.date_created`]="{ item }">
          {{ $date(item.date_created) }}
        </template>
        <template #[`item.action`]="{ item }">
          <v-chip
            :color="
              item.action === 'core.login.succeeded' ? 'success' : 'error'
            "
            :prepend-icon="
              item.action === 'core.login.succeeded'
                ? 'mdi-check-circle-outline'
                : 'mdi-alert-circle-outline'
            "
            size="small"
            label
          >
            {{ item.action_label }}
          </v-chip>
        </template>
      </v-data-table>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import accountApi from '@/api/account'

const { $gettext } = useGettext()
const loading = ref(true)
const logins = ref([])

const headers = [
  { title: $gettext('Date'), key: 'date_created', sortable: false },
  { title: $gettext('Result'), key: 'action', sortable: false },
  { title: $gettext('IP address'), key: 'ip_address', sortable: false },
]

onMounted(async () => {
  try {
    const resp = await accountApi.getLoginHistory()
    logins.value = resp.data
  } finally {
    loading.value = false
  }
})
</script>
