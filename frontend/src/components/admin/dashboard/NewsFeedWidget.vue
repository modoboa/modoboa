<template>
  <v-card v-if="news.length" :title="$gettext('Latest news')">
    <v-card-text>
      <v-list density="compact">
        <v-list-item v-for="item in news" :key="item.link" class="px-0">
          <v-list-item-subtitle>
            {{ formatDate(item.published) }}
          </v-list-item-subtitle>
          <v-list-item-title class="text-wrap">
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
          </v-list-item-title>
        </v-list-item>
      </v-list>
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
import { DateTime } from 'luxon'
import { useGettext } from 'vue3-gettext'
import adminApi from '@/api/admin'
import { localeToBCP47 } from '@/utils'

const gettext = useGettext()

const news = ref([])

// ponytail: fixed window, not per-user "unread" tracking; add that if the badge feels stale
const RECENT_DAYS = 30

// The time of day is useless for news
function formatDate(value) {
  return DateTime.fromISO(value)
    .setLocale(localeToBCP47(gettext.current))
    .toLocaleString(DateTime.DATE_MED)
}

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
