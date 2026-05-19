<template>
  <LoadingData v-if="!domain" />
  <div v-else>
    <v-toolbar flat>
      <v-toolbar-title>
        {{ $gettext('Domain') }} {{ domain.name }}
        <v-btn
          color="primary"
          icon="mdi-circle-edit-outline"
          :to="{ name: 'DomainEdit', params: { id: domain.pk } }"
        ></v-btn>
        <v-btn
          color="primary"
          icon="mdi-reload"
          @click="refreshDomain()"
        ></v-btn>
      </v-toolbar-title>
    </v-toolbar>

    <v-tabs v-model="tab" class="mb-4" color="primary">
      <v-tab>
        {{ $gettext('General') }}
      </v-tab>
      <v-tab>
        {{ $gettext('Statistics') }}
      </v-tab>
      <v-tab>
        {{ $gettext('DMARC') }}
      </v-tab>
      <v-tab v-for="extraTab in pluginTabs" :key="extraTab.name">
        {{ extraTab.title }}
      </v-tab>
    </v-tabs>

    <v-tabs-window v-model="tab">
      <v-tabs-window-item>
        <v-row>
          <v-col cols="12" md="6">
            <DomainSummary :domain="domain" />
            <div class="mt-4" />
            <template v-if="domain.type === 'relaydomain'">
              <RelayDomainSummary :domain="domain" />
              <div class="mt-4" />
            </template>
            <DomainAdminList :domain="domain" />
            <div class="mt-4" />
            <DomainPolicy v-if="isAmavisEnabled" :domain="domain" />
            <template v-for="block in pluginLeftBlocks" :key="block.name">
              <div class="mt-4" />
              <component
                :is="block.component"
                :domain="domain"
                v-bind="block.props || {}"
                @refresh="refreshDomain"
              />
            </template>
          </v-col>
          <v-col cols="12" md="6">
            <DNSDetail v-model="domain" />
            <div class="mt-4" />
            <ResourcesForm
              v-if="
                limitsConfig.params &&
                limitsConfig.params.enable_domain_limits &&
                domain.resources &&
                domain.resources.length
              "
              :resources="domain.resources"
            />
            <template v-for="block in pluginRightBlocks" :key="block.name">
              <div class="mt-4" />
              <component
                :is="block.component"
                :domain="domain"
                v-bind="block.props || {}"
                @refresh="refreshDomain"
              />
            </template>
          </v-col>
        </v-row>
      </v-tabs-window-item>
      <v-tabs-window-item>
        <v-row>
          <v-col cols="12">
            <TimeSerieChart
              v-if="domain.name"
              :domain="domain"
              graphic-set="mailtraffic"
              graphic-name="averagetraffic"
            />
          </v-col>
          <v-col cols="12">
            <TimeSerieChart
              v-if="domain.name"
              :domain="domain"
              graphic-set="mailtraffic"
              graphic-name="averagetrafficsize"
            />
          </v-col>
        </v-row>
      </v-tabs-window-item>
      <v-tabs-window-item>
        <DmarcAligmentChart :domain="domain" />
      </v-tabs-window-item>
      <v-tabs-window-item v-for="extraTab in pluginTabs" :key="extraTab.name">
        <component
          :is="extraTab.component"
          :domain="domain"
          v-bind="extraTab.props || {}"
          @refresh="refreshDomain"
        />
      </v-tabs-window-item>
    </v-tabs-window>
  </div>
</template>

<script setup>
import DomainAdminList from '@/components/admin/domains/DomainAdminList.vue'
import DmarcAligmentChart from '@/components/admin/dmarc/DmarcAligmentChart.vue'
import DNSDetail from '@/components/admin/domains/DNSDetail.vue'
import DomainSummary from '@/components/admin/domains/DomainSummary.vue'
import RelayDomainSummary from '@/components/admin/domains/RelayDomainSummary.vue'
import DomainPolicy from '@/components/admin/domains/DomainPolicy.vue'
import LoadingData from '@/components/tools/LoadingData.vue'
import ResourcesForm from '@/components/tools/ResourcesForm.vue'
import TimeSerieChart from '@/components/tools/TimeSerieChart.vue'
import { useGettext } from 'vue3-gettext'
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useGlobalStore, usePluginsStore } from '@/stores'
import domainsApi from '@/api/domains'
import parametersApi from '@/api/parameters'

const { $gettext } = useGettext()
const route = useRoute()
const globalStore = useGlobalStore()
const pluginsStore = usePluginsStore()

const PLUGIN_BLOCKS_EXTENSION_POINT = 'domain.detail.general.blocks'
const PLUGIN_TABS_EXTENSION_POINT = 'domain.detail.tabs'

const domain = ref(null)
const limitsConfig = ref({})
const tab = ref(null)

const isAmavisEnabled = computed(() => {
  return 'amavis' in globalStore.capabilities
})

function appliesToDomain(item) {
  return (
    !Array.isArray(item.applies_to) ||
    item.applies_to.length === 0 ||
    item.applies_to.includes(domain.value?.type)
  )
}

const pluginBlocks = computed(() =>
  pluginsStore
    .uiExtensions(PLUGIN_BLOCKS_EXTENSION_POINT)
    .filter(appliesToDomain)
)
const pluginLeftBlocks = computed(() =>
  pluginBlocks.value.filter((block) => block.column === 'left')
)
const pluginRightBlocks = computed(() =>
  pluginBlocks.value.filter((block) => block.column !== 'left')
)
const pluginTabs = computed(() =>
  pluginsStore.uiExtensions(PLUGIN_TABS_EXTENSION_POINT).filter(appliesToDomain)
)

async function refreshDomain() {
  domainsApi.getDomain(route.params.id).then((resp) => {
    domain.value = resp.data
  })
}

const resp = await parametersApi.getGlobalApplication('limits')
limitsConfig.value = resp.data

await refreshDomain()
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
.v-tabs-items {
  background-color: #f7f8fa !important;
}
</style>

<style>
.v-window__container {
  width: 100% !important;
}
</style>
