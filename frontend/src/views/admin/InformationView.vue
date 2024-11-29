<template>
  <div>
    <v-toolbar flat>
      <v-toolbar-title>{{ $gettext('Information') }}</v-toolbar-title>
    </v-toolbar>
    <v-card v-if="globalStore.notifications.length" class="my-6">
      <v-card-title>
        {{ $gettext('Important messages') }}
      </v-card-title>

      <v-card-text>
        <v-alert
          v-for="notification in globalStore.notifications"
          :key="notification.id"
          :type="notification.level"
          :title="notification.text"
          border="start"
          variant="tonal"
        >
          <template v-if="notification.id === 'deprecatedpasswordscheme'">
            {{
              $gettext(
                'The password scheme you are using has been deprecated and will be removed in the next minor version. The procedure to upgrade to a stronger scheme is as follows:'
              )
            }}
            <ol class="mt-4">
              <li
                v-html="
                  $gettext(
                    'Go to <strong>Settings > General</strong> section',
                    true
                  )
                "
              ></li>
              <li
                v-html="
                  $gettext(
                    'Change the value of <strong>Default password scheme</strong>',
                    true
                  )
                "
              ></li>
              <li
                v-html="
                  $gettext(
                    'Make sure <strong>Update password scheme at login</strong> option is enabled',
                    true
                  )
                "
              ></li>
              <li v-html="$gettext('Save your changes')"></li>
              <li>
                {{
                  $gettext(
                    'Logout / Login with your current account so its password gets updated'
                  )
                }}
              </li>
              <li
                v-html="
                  $gettext(
                    'Inform <strong>ALL</strong> your users that they must login to Modoboa to complete the operation',
                    true
                  )
                "
              ></li>
            </ol>
            <p
              class="mt-4"
              v-html="
                $gettext(
                  'You must apply this procedure <strong>BEFORE</strong> you install a newest version of Modoboa, otherwise <strong>you will be unable to connect to the web interface anymore</strong>.',
                  true
                )
              "
            ></p>
            <p
              class="mt-4"
              v-html="
                $gettext(
                  'Please note that you will see this message until <strong>ALL</strong> user passwords have been converted using the new scheme.',
                  true
                )
              "
            ></p>
          </template>
        </v-alert>
      </v-card-text>
    </v-card>
    <v-card class="mt-6">
      <v-card-title>
        {{ $gettext('Installed components') }}
      </v-card-title>
      <v-card-text>
        <v-alert
          v-if="updatesAvailable"
          variant="tonal"
          type="success"
          text
          border="start"
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

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useGlobalStore } from '@/stores'
import adminApi from '@/api/admin'

const { $gettext } = useGettext()
const globalStore = useGlobalStore()

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
