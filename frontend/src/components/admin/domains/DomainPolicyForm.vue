<template>
  <v-card>
    <v-card-title class="text-h5">
      <span> {{ $gettext('Content filter settings') }} </span>
    </v-card-title>
    <v-card-text>
      <v-row>
        <v-col cols="6">
          <YesNoDefaultField
            v-model="form.bypass_virus_checks"
            :label="$gettext('Disable virus checks')"
            color="primary"
            hide-details
          />

          <YesNoDefaultField
            v-model="form.bypass_spam_checks"
            :label="$gettext('Disable spam checks')"
            color="primary"
            class="mt-6"
            hide-details
          />

          <YesNoDefaultField
            v-model="form.bypass_banned_checks"
            :label="$gettext('Disable banned checks')"
            color="primary"
            class="mt-6"
            hide-details
          />
        </v-col>
        <v-col cols="6">
          <div>
            <label class="v-label mb-4">{{ $gettext('Spam marker') }}</label>
            <v-row>
              <v-col cols="9">
                <v-text-field
                  v-model="form.spam_subject_tag2"
                  variant="outlined"
                  density="compact"
                  :disabled="useDefaultMarker"
                />
              </v-col>
              <v-col cols="3">
                <v-checkbox
                  v-model="useDefaultMarker"
                  :label="$gettext('default')"
                  color="primary"
                  density="compact"
                  hide-details
                  @update:model-value="clearSpamMarker"
                />
              </v-col>
            </v-row>
          </div>
          <div class="v-label mb-4">{{ $gettext('Thresholds') }}</div>
          <v-row class="align-center">
            <v-col cols="4">
              <v-text-field
                v-model="form.spam_tag2_level"
                variant="outlined"
                density="compact"
                type="number"
                hide-details
              >
              </v-text-field>
            </v-col>
            <v-col cols="8">
              {{ $gettext('or more is spam') }}
            </v-col>
          </v-row>
          <v-row class="align-center">
            <v-col cols="4">
              <v-text-field
                v-model="form.spam_kill_level"
                variant="outlined"
                density="compact"
                type="number"
                hide-details
              >
              </v-text-field>
            </v-col>
            <v-col cols="8">
              {{ $gettext('or more throw spam message away') }}
            </v-col>
          </v-row>
        </v-col>
      </v-row>
    </v-card-text>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn :loading="loading" @click="emit('close')">
        {{ $gettext('Cancel') }}
      </v-btn>
      <v-btn color="primary" :loading="loading" @click="submit">
        {{ $gettext('Apply') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'
import YesNoDefaultField from '@/components/tools/YesNoDefaultField'
import api from '@/api/amavis'

const props = defineProps({
  domainId: {
    type: Number,
    default: null,
  },
  modelValue: {
    type: Object,
    default: () => {},
  },
})
const emit = defineEmits(['close', 'update:modelValue'])

const form = ref({})
const loading = ref(false)
const useDefaultMarker = ref(false)

form.value = {
  bypass_virus_checks:
    props.modelValue.bypass_virus_checks === null
      ? ''
      : props.modelValue.bypass_virus_checks,
  bypass_spam_checks:
    props.modelValue.bypass_spam_checks === null
      ? ''
      : props.modelValue.bypass_spam_checks,
  bypass_banned_checks:
    props.modelValue.bypass_banned_checks === null
      ? ''
      : props.modelValue.bypass_banned_checks,
  spam_tag2_level: props.modelValue.spam_tag2_level,
  spam_kill_level: props.modelValue.spam_kill_level,
  spam_subject_tag2: props.modelValue.spam_subject_tag2,
}

if (form.value.spam_subject_tag2 === null) {
  useDefaultMarker.value = true
}

const clearSpamMarker = (value) => {
  if (value) {
    form.value.spam_subject_tag2 = null
  }
}

const submit = async () => {
  loading.value = true
  const data = { ...form.value }
  if (data.spam_tag2_level === '') {
    data.spam_tag2_level = null
  }
  if (data.spam_kill_level === '') {
    data.spam_kill_level = null
  }
  try {
    const resp = await api.updateDomainPolicy(props.domainId, data)
    emit('update:modelValue', resp.data)
    emit('close')
  } finally {
    loading.value = false
  }
}
</script>
