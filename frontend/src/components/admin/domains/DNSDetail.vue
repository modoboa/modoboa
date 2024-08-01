<template>
  <v-card v-if="domain">
    <v-card-title>
      <span> DNS </span>
      <v-btn
        class="ml-2"
        icon="mdi-information-outline"
        :title="$gettext('DNS configuration help')"
        variant="text"
        density="compact"
        @click="showConfigHelp = true"
      ></v-btn>
    </v-card-title>
    <v-card-text>
      <translate class="overline">MX records</translate>
      <template v-if="domain.dns_global_status == 'pending'">
        <v-row>
          <v-col>
            <v-chip color="info" size="small">
              {{ $gettext('Pending') }}
            </v-chip>
          </v-col>
        </v-row>
      </template>
      <template v-else>
        <v-data-table-virtual
          :headers="mxRecordHeaders"
          :items="detail.mx_records"
        >
          <template #[`item.updated`]="{ item }">
            {{ $date(item.updated) }}
          </template>
        </v-data-table-virtual>
      </template>
      <div class="overline">{{ $gettext('Auto configuration') }}</div>
      <template v-if="domain.dns_global_status == 'pending'">
        <v-row>
          <v-col>
            <v-chip color="info" size="small">
              {{ $gettext('Pending') }}
            </v-chip>
          </v-col>
        </v-row>
      </template>
      <template v-else>
        <v-row>
          <v-col>
            <v-chip v-if="detail.autoconfig_record" color="success">
              {{
                $gettext('autoconfig record (Mozilla): %{ value }', {
                  value: detail.autoconfig_record.value,
                })
              }}
            </v-chip>
            <v-chip v-else color="warning">
              {{ $gettext('autoconfig record (Mozilla) not found') }}
            </v-chip>
          </v-col>
          <v-col>
            <v-chip v-if="detail.autodiscover_record" color="success">
              {{
                $gettext('autodiscover record (Microsoft): %{ value }', {
                  value: detail.autodiscover_record.value,
                })
              }}
            </v-chip>
            <v-chip v-else color="warning">
              {{ $gettext('autodiscover record (Microsoft) not found') }}
            </v-chip>
          </v-col>
        </v-row>
        <div class="overline">{{ $gettext('Authentication') }}</div>
        <v-row>
          <v-col>
            <v-chip v-if="detail.spf_record" color="success">
              {{ $gettext('SPF record found') }}
            </v-chip>
            <v-chip v-else color="error">
              {{ $gettext('SPF record not found') }}
            </v-chip>
          </v-col>
          <v-col>
            <v-chip v-if="detail.dkim_record" color="success">
              {{ $gettext('DKIM record found') }}
            </v-chip>
            <v-chip v-else color="error">
              {{ $gettext('DKIM record not found') }}
            </v-chip>
          </v-col>
          <v-col>
            <v-chip v-if="detail.dmarc_record" color="success">
              {{ $gettext('DMARC record found') }}
            </v-chip>
            <v-chip v-else color="error">
              {{ $gettext('DMARC record not found') }}
            </v-chip>
          </v-col>
        </v-row>
      </template>
      <template v-if="domain.enable_dkim">
        <div class="d-flex align-center flex-nowrap mt-4">
          <div class="text-subtitle-2">
            {{ $gettext('DKIM key') }}
          </div>
          <div class="ml-6">
            <div v-if="domain.dkim_private_key_path && domain.dkim_public_key">
              <v-btn color="primary" size="small" @click="showDKIMKey = true">
                {{ $gettext('Show key') }}
              </v-btn>
              <v-btn
                icon="mdi-content-copy"
                variant="text"
                class="ml-2"
                :title="$gettext('Copy key to clipboard')"
                @click="copyPubKey"
              ></v-btn>
              <v-btn
                icon="mdi-refresh"
                :title="$gettext('Generate a new DKIM key')"
                variant="text"
                :loading="keyLoading"
                @click="generateNewKey"
              ></v-btn>
            </div>
            <div v-else>
              {{ $gettext('Not generated') }}
              <v-btn
                icon="mdi-reload"
                color="primary"
                variant="text"
                :loading="keyLoading"
                @click="retryKeyGeneration"
              ></v-btn>
            </div>
          </div>
        </div>
      </template>
    </v-card-text>
    <v-dialog v-model="showConfigHelp" max-width="800px" persistent>
      <DomainDNSConfig :domain="domain" @close="showConfigHelp = false" />
    </v-dialog>
    <v-dialog v-model="showDKIMKey" max-width="800px" persistent>
      <DomainDKIMKey :domain="domain" @close="showDKIMKey = false" />
    </v-dialog>
    <ConfirmDialog ref="dialog" />
  </v-card>
</template>

<script setup lang="js">
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import domainsApi from '@/api/domains'
import DomainDKIMKey from './DomainDKIMKey.vue'
import DomainDNSConfig from './DomainDNSConfig.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import { ref, computed, watch } from 'vue'

const { $gettext } = useGettext()
const busStore = useBusStore()

const props = defineProps({
  modelValue: { type: Object, default: null },
})

const domain = computed(() => props.modelValue)

const dialog = ref()
const detail = ref({})
const mxRecordHeaders = ref([
  { title: $gettext('Name'), value: 'name' },
  { title: $gettext('Address'), value: 'address' },
  { title: $gettext('Updated'), value: 'updated' },
])
const keyLoading = ref(false)

const showConfigHelp = ref(false)
const showDKIMKey = ref(false)

function copyPubKey() {
  navigator.clipboard.writeText(domain.value.dkim_public_key)
  busStore.displayNotification({
    msg: $gettext('DKIM key copied to clipboard'),
    type: 'success',
  })
}

function confirmGenNewKey() {
  const payload = {
    dkim_private_key_path: '',
  }
  domainsApi
    .patchDomain(domain.value.pk, payload)
    .then(() => {
      busStore.displayNotification({
        msg: $gettext(
          'A new key will be generated soon. Refresh the page in a moment to see it.'
        ),
        type: 'success',
      })
      domain.value.dkim_private_key_path = ''
      keyLoading.value = false
    })
    .catch(() => {
      keyLoading.value = false
    })
}

function cancelDKIMGen() {
  keyLoading.value = false
}

async function retryKeyGeneration() {
  keyLoading.value = true
  domainsApi.getDomainDNSDetail(domain.value.pk).then(async (resp) => {
    detail.value = resp.data
    const result = await dialog.value.open(
      $gettext('warning'),
      $gettext(
        'DKIM key does not seem to be generated yet or has failed. Do you want to requeue the job?'
      ),
      {
        color: 'warning',
        cancelLabel: $gettext('No'),
        agreeLabel: $gettext('Yes'),
      }
    )
    if (result) {
      confirmGenNewKey()
    } else {
      cancelDKIMGen()
    }
  })
}

function generateNewKey() {
  dialog.value.open(
    $gettext('Warning'),
    $gettext(
      'DKIM keys already exist for this domain. Do you want to overwrite them?'
    ),
    {
      color: 'error',
      cancelLabel: $gettext('No'),
      agreeLabel: $gettext('Yes'),
    }
  )
}

watch(
  domain,
  (newDomain) => {
    if (newDomain) {
      domainsApi.getDomainDNSDetail(newDomain.pk).then((resp) => {
        detail.value = resp.data
      })
    }
  },
  { immediate: true }
)
</script>
