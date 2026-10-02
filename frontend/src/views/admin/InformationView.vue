<template>
  <div>
    <v-toolbar flat>
      <v-toolbar-title>{{ $gettext('Information') }}</v-toolbar-title>
    </v-toolbar>
    <v-card v-if="globalStore.adminNotifications.length" class="my-6">
      <v-card-title>
        {{ $gettext('Important messages') }}
      </v-card-title>

      <v-card-text>
        <v-alert
          v-for="notification in globalStore.adminNotifications"
          :key="notification.id"
          :type="notification.color"
          border="start"
          variant="tonal"
          class="mb-2"
        >
          <div class="text-high-emphasis">
            <div class="font-weight-medium">{{ notification.text }}</div>
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
          </div>
        </v-alert>
      </v-card-text>
    </v-card>
    <v-card class="mt-6">
      <v-tabs
        :model-value="tab"
        color="primary"
        @update:model-value="changeTab"
      >
        <v-tab value="components">
          {{ $gettext('Installed components') }}
        </v-tab>
        <v-tab v-if="proTabVisible" value="pro">
          <v-icon
            icon="mdi-star-four-points"
            color="secondary"
            size="small"
            start
          />
          Modoboa Pro
        </v-tab>
      </v-tabs>
      <v-divider />
      <v-tabs-window :model-value="tab">
        <v-tabs-window-item value="components">
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
              <div tag="p" class="text-body-medium">
                {{
                  $gettext(
                    'Check out the following list to find related components'
                  )
                }}
              </div>
            </v-alert>
            <v-data-table-virtual
              :headers="headers"
              :items="tableItems"
              :row-props="getRowProps"
            >
              <template #[`item.name`]="{ item }">
                <template v-if="item.promotion">
                  <v-icon
                    icon="mdi-star-four-points-outline"
                    color="secondary"
                    size="small"
                    class="mr-2"
                  />
                  {{ item.name }}
                </template>
                <template v-else>{{ item.name }}</template>
              </template>
              <template #[`item.version`]="{ item }">
                <v-chip v-if="item.promotion" size="small" variant="outlined">
                  {{ $gettext('Not installed') }}
                </v-chip>
                <template v-else>{{ item.version }}</template>
              </template>
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
              <template #[`item.description`]="{ item }">
                {{ item.description }}
                <router-link
                  v-if="item.promotion"
                  :to="{ name: 'ModoboaPro' }"
                  class="ml-1"
                >
                  {{ $gettext('Learn more') }}
                </router-link>
              </template>
            </v-data-table-virtual>
          </v-card-text>
        </v-tabs-window-item>
        <v-tabs-window-item v-if="proTabVisible" value="pro">
          <v-card-text>
            <template v-if="proInstalled">
              <template v-if="proExtensions.length">
                <component
                  :is="extension.component"
                  v-for="extension in proExtensions"
                  :key="extension.name"
                  v-bind="extension.props || {}"
                />
              </template>
              <v-alert v-else type="success" variant="tonal">
                {{ $gettext('Modoboa Pro is installed.') }}
              </v-alert>
            </template>
            <ProPromotion v-else />
          </v-card-text>
        </v-tabs-window-item>
      </v-tabs-window>
    </v-card>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useGlobalStore, usePluginsStore } from '@/stores'
import adminApi from '@/api/admin'
import constants from '@/constants.json'
import ProPromotion from '@/components/admin/information/ProPromotion.vue'

const PRO_EXTENSION_POINT = 'admin.information.pro'

const props = defineProps({
  tab: {
    type: String,
    default: 'components',
  },
})

const { $gettext } = useGettext()
const router = useRouter()
const globalStore = useGlobalStore()
const pluginsStore = usePluginsStore()

const components = ref([])
const headers = [
  { title: $gettext('Name'), value: 'name' },
  { title: $gettext('Installed version'), value: 'version' },
  { title: $gettext('Latest version'), value: 'last_version' },
  { title: $gettext('Description'), value: 'description' },
]

const proInstalled = computed(() =>
  pluginsStore.isInstalled(constants.PRO_PLUGIN_NAME)
)
const proPromotionEnabled = computed(
  () => 'pro_promotion' in globalStore.capabilities
)
const proTabVisible = computed(
  () => proInstalled.value || proPromotionEnabled.value
)
const proExtensions = computed(() =>
  pluginsStore.uiExtensions(PRO_EXTENSION_POINT)
)
const tab = computed(() =>
  props.tab === 'pro' && proTabVisible.value ? 'pro' : 'components'
)

const tableItems = computed(() => {
  if (proInstalled.value || !proPromotionEnabled.value) {
    return components.value
  }
  return [
    ...components.value,
    {
      name: constants.PRO_PLUGIN_NAME,
      description: $gettext(
        'Virtual hosts, automatic HTTPS and per-customer branding'
      ),
      promotion: true,
    },
  ]
})

const updatesAvailable = computed(
  () => components.value.filter((item) => item.update).length > 0
)

function changeTab(value) {
  router.push({ name: value === 'pro' ? 'ModoboaPro' : 'Information' })
}

function getRowProps({ item }) {
  if (item.update) {
    return { class: 'bg-green-lighten-5' }
  }
  if (item.promotion) {
    return { class: 'text-medium-emphasis' }
  }
  return {}
}

onMounted(() => {
  adminApi.getComponentsInformation().then((resp) => {
    components.value = resp.data
  })
})
</script>

<style scoped lang="scss">
.v-toolbar {
  background-color: #f7f8fa !important;
}

a {
  text-decoration: none;
  color: rgb(var(--v-theme-primary));

  &:visited {
    color: rgb(var(--v-theme-primary));
  }
}
</style>
