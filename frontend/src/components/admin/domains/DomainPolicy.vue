<template>
  <div>
    <v-card v-if="policy">
      <v-card-title>
        <span>{{ $gettext('Content filter') }}</span>
        <v-btn
          class="ml-2"
          icon="mdi-circle-edit-outline"
          :title="$gettext('Edit content filter settings')"
          variant="text"
          density="compact"
          @click="showEditForm = true"
        ></v-btn>
      </v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="6">{{ $gettext('Spam filters') }}</v-col>
          <v-col cols="6">
            <BooleanIcon
              v-if="
                policy.bypass_spam_checks !== null &&
                policy.bypass_spam_checks !== ''
              "
              :value="policy.bypass_spam_checks !== 'Y'"
              variant="flat"
            />
            <span v-else>{{ $gettext('Default value') }}</span>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">{{ $gettext('Virus filters') }}</v-col>
          <v-col cols="6">
            <BooleanIcon
              v-if="
                policy.bypass_virus_checks !== null &&
                policy.bypass_virus_checks !== ''
              "
              :value="policy.bypass_virus_checks !== 'Y'"
              variant="flat"
            />
            <span v-else>{{ $gettext('Default value') }}</span>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">{{ $gettext('Banned filters') }}</v-col>
          <v-col cols="6">
            <BooleanIcon
              v-if="
                policy.bypass_banned_checks !== null &&
                policy.bypass_banned_checks !== ''
              "
              :value="policy.bypass_banned_checks !== 'Y'"
              variant="flat"
            />
            <span v-else>{{ $gettext('Default value') }}</span>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">{{
            $gettext('Spam classification threshold')
          }}</v-col>
          <v-col cols="6">
            <span v-if="policy.spam_tag2_level !== null">
              {{ policy.spam_tag2_level }}
            </span>
            <span v-else>{{ $gettext('Default value') }}</span>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">{{ $gettext('Rejection threshold') }}</v-col>
          <v-col cols="6">
            <span v-if="policy.spam_kill_level !== null">
              {{ policy.spam_kill_level }}
            </span>
            <span v-else>{{ $gettext('Default value') }}</span>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">{{ $gettext('Spam marker') }}</v-col>
          <v-col cols="6">
            <span v-if="policy.spam_subject_tag2 !== null">
              {{ policy.spam_subject_tag2 }}
            </span>
            <span v-else>{{ $gettext('Default value') }}</span>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
    <v-dialog v-model="showEditForm" width="1000">
      <DomainPolicyForm
        v-model="policy"
        :domain-id="props.domain.pk"
        @close="showEditForm = false"
      />
    </v-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import BooleanIcon from '@/components/tools/BooleanIcon'
import DomainPolicyForm from './DomainPolicyForm'
import api from '@/api/amavis'

const props = defineProps({
  domain: {
    type: Object,
    default: null,
  },
})

const policy = ref(null)
const showEditForm = ref(false)

const resp = await api.getDomainPolicy(props.domain.pk)
policy.value = resp.data
</script>
