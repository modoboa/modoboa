<template>
  <v-card class="mt-6">
    <v-data-table-server
      v-model="selected"
      :headers="headers"
      :items="messages"
      :search="search"
      :loading="loading"
      :items-length="totalMessages"
      :page="currentPage"
      :items-per-page="itemsPerPageR"
      item-value="pk"
      elevation="0"
      show-select
      :sort-by="sortByR"
      @update:options="updatedOptions"
    >
      <template #top>
        <v-text-field
          v-model="search"
          prepend-inner-icon="mdi-magnify"
          :placeholder="$gettext('Search in messages')"
          variant="outlined"
          single-line
          flat
          hide-details
          density="compact"
          class="flex-grow-0 w-33 mr-4"
          clearable
          @click:clear="fetchContent"
          @keyup.enter="submitSearch"
        ></v-text-field>
      </template>
    </v-data-table-server>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/api/amavis'

const messages = ref([])
const search = ref('')
const totalMessages = ref(0)

const fetchContent = () => {}

const submitSearch = () => {}
</script>
