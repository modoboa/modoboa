<template>
  <div>
    <v-toolbar flat>
      <v-toolbar-title>{{ $gettext('Information') }}</v-toolbar-title>
    </v-toolbar>
    <v-card class="mt-6">
      <v-card-title>
        {{ $gettext('Installed components') }}
      </v-card-title>
      <v-card-text>
        <v-alert
          v-if="updatesAvailable"
          variant="outlined"
          type="success"
          text
          border="left"
        >
          <div tag="p">
            {{ $gettext('One or more updates are available') }}
          </div>
          <div tag="p" class="text-body-2">
            {{
              $gettext(
                'Check out the following list to find related components'
              )
            }}
          </div>
        </v-alert>
        <v-data-table-virtual
          :headers="headers"
          :items="components"
          :item-class="getItemBackground"
        >
          <template #[`item.last_version`]="{ item }">
            <template v-if="item.changelog_url">
              <a :href="item.changelog_url" target="_blank">{{
                item.last_version
              }}</a>
            </template>
            <template v-else>
              {{ item.last_version }}
            </template>
          </template>
        </v-data-table-virtual>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="js">
import { useGettext } from 'vue3-gettext'
import adminApi from '@/api/admin'
import { computed, ref, onMounted } from 'vue'

const { $gettext } = useGettext()

const components = ref([])
const headers = [
  { title: $gettext('Name'), value: 'name' },
  { title: $gettext('Installed version'), value: 'version' },
  { title: $gettext('Latest version'), value: 'last_version' },
  { title: $gettext('Description'), value: 'description' },
]

const updatesAvailable = computed(
  () => components.value.filter((item) => item.update).length > 0
)

function getItemBackground(item) {
  if (item.update) {
    return 'green lighten-5'
  }
  return ''
}

onMounted(() => {
  adminApi.getComponentsInformation().then((resp) => {
    components.value = resp.data
  })
})
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
