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
    </v-tabs>

    <v-tabs-window v-model="tab">
      <v-tabs-window-item>
        <v-row>
          <v-col cols="12" md="6">
            <DomainSummary :domain="domain" />
            <div class="mt-4" />
            <DomainAdminList :domain="domain" />
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
    </v-tabs-window>
  </div>
</template>

<script setup lang="js">
import DomainAdminList from '@/components/admin/domains/DomainAdminList.vue'
import DmarcAligmentChart from '@/components/admin/dmarc/DmarcAligmentChart.vue'
import DNSDetail from '@/components/admin/domains/DNSDetail.vue'
import DomainSummary from '@/components/admin/domains/DomainSummary.vue'
import LoadingData from '@/components/tools/LoadingData.vue'
import ResourcesForm from '@/components/tools/ResourcesForm.vue'
import TimeSerieChart from '@/components/tools/TimeSerieChart.vue'
import { useGettext } from 'vue3-gettext'
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import domainsApi from '@/api/domains'

const { $gettext } = useGettext()
const route = useRoute()

const domain = ref(null)
const limitsConfig = ref({})
const tab = ref(null)

function refreshDomain() {
  domainsApi.getDomain(route.params.id).then((resp) => {
    domain.value = resp.data
  })
}

refreshDomain()
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
