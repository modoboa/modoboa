<template>
  <v-card :title="$gettext('Latest news')">
    <v-card-text>
      <v-data-table
        :headers="headers"
        :items="news"
        hide-default-header
        hide-default-footer
      >
        <template #[`item.title`]="{ item }">
          <a
            :href="item.link"
            target="_blank"
            :class="{ 'font-weight-bold': isRecent(item) }"
            >{{ item.title }}</a
          >
          <v-chip
            v-if="isRecent(item)"
            size="x-small"
            color="primary"
            variant="flat"
            class="ml-2"
          >
            {{ $gettext('New') }}
          </v-chip>
        </template>
        <template #[`item.published`]="{ item }">
          {{ $date(item.published) }}
        </template>
      </v-data-table>
    </v-card-text>
    <v-card-actions class="justify-center">
      <div>
        <a href="https://modoboa.org/weblog/" target="_blank">
          {{ $gettext('Visit the official weblog for more information') }}
        </a>
      </div>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'
import adminApi from '@/api/admin'

const news = ref([])

const headers = [
  { title: '', key: 'title' },
  { title: '', key: 'published', align: 'end' },
]

// ponytail: fixed window, not per-user "unread" tracking; add that if the badge feels stale
const RECENT_DAYS = 30

function isRecent(item) {
  return Date.now() - new Date(item.published) < RECENT_DAYS * 24 * 3600 * 1000
}

const resp = await adminApi.getNewsFeed()
news.value = resp.data
</script>

<style scoped lang="scss">
a {
  text-decoration: none;
  color: rgb(var(--v-theme-primary));

  &:visited {
    color: rgb(var(--v-theme-primary));
  }
}
</style>
