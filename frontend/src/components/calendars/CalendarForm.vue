<template>
  <v-card>
    <v-form ref="formRef" @submit.prevent="submit">
      <v-card-title>
        <span v-if="calendar.pk" class="headline">{{
          $gettext('Edit calendar')
        }}</span>
        <span v-else class="modal-title">{{ $gettext('New calendar') }}</span>
      </v-card-title>
      <v-card-text class="py-4">
        <v-row no-gutters>
          <v-col cols="12">
            <v-text-field
              v-model="calendar.name"
              :label="$gettext('Name')"
              variant="outlined"
              density="compact"
              :rules="[rules.required]"
              :error-messages="formErrors.name"
            />
          </v-col>
          <v-col cols="12">
            <v-color-picker
              v-model="calendar.color"
              :label="$gettext('Color')"
              class="ma-2"
              swatches-max-height="200px"
              show-swatches
              hide-inputs
              :rules="[rules.required]"
            ></v-color-picker>
          </v-col>
        </v-row>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="close">{{ $gettext('Close') }}</v-btn>
        <v-btn color="primary" type="submit">
          {{ submitLabel }}
        </v-btn>
      </v-card-actions>
    </v-form>
  </v-card>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import rules from '@/plugins/rules'
import calendarsApi from '@/api/calendars'

const emit = defineEmits(['close', 'colorChanged'])
const props = defineProps({
  initialCalendar: {
    type: Object,
    default: () => {
      return { color: '' }
    },
  },
})

const { $gettext } = useGettext()
const busStore = useBusStore()

onMounted(() => {
  calendar.value = { ...props.initialCalendar }
  shared.value = props.initialCalendar.domain !== undefined
})

const calendar = ref({})
const shared = ref(false)
const formErrors = ref({})
const formRef = ref()

const submitLabel = computed(() => {
  if (calendar.value.pk) {
    return $gettext('Update')
  }
  return $gettext('Create')
})

function close() {
  calendar.value = {}
  shared.value = false
  formErrors.value = {}
  emit('close')
}

async function submit() {
  const { valid } = await formRef.value.validate()
  if (!valid) {
    return
  }
  let msg
  if (calendar.value.pk) {
    await calendarsApi.updateUserCalendar(calendar.value.pk, calendar.value)
    msg = $gettext('Calendar updated')
  } else {
    await calendarsApi.createUserCalendar(calendar.value)
    msg = $gettext('Calendar created')
  }
  if (props.initialCalendar.color !== calendar.value.color) {
    emit('colorChanged', calendar.value)
  }
  close()
  busStore.displayNotification({
    msg,
  })
}
</script>
