<template>
  <v-card>
    <v-card-title>
      <span class="headline">{{ $gettext('Calendar color') }}</span>
    </v-card-title>
    <v-card-subtitle>
      {{ calendar.name }} ({{ calendar.owner }})
    </v-card-subtitle>
    <v-card-text class="py-4">
      <v-color-picker
        v-model="color"
        mode="hex"
        :modes="['hex']"
        class="ma-2"
        swatches-max-height="200px"
        show-swatches
        hide-inputs
      ></v-color-picker>
      <div v-if="formErrors.color" class="text-error">
        {{ formErrors.color.join(' ') }}
      </div>
    </v-card-text>
    <v-card-actions>
      <v-btn :loading="working" @click="save('')">
        {{ $gettext("Owner's color") }}
      </v-btn>
      <v-spacer />
      <v-btn :loading="working" @click="close">{{ $gettext('Close') }}</v-btn>
      <v-btn color="primary" :loading="working" @click="save(color)">
        {{ $gettext('Update') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import api from '@/api/calendars'

// Color of a calendar shared with the current user: it only applies to them
const props = defineProps({
  calendar: {
    type: Object,
    required: true,
  },
})
const emit = defineEmits(['close', 'colorChanged'])

const { $gettext } = useGettext()
const busStore = useBusStore()

const color = ref(props.calendar.color)
const formErrors = ref({})
const working = ref(false)

function close() {
  formErrors.value = {}
  emit('close')
}

/**
 * Save the color of the calendar, an empty value restores the owner's one.
 */
async function save(value) {
  working.value = true
  try {
    await api.patchCalendarSharedWithMe(props.calendar.pk, { color: value })
    busStore.displayNotification({ msg: $gettext('Calendar updated') })
    emit('colorChanged', props.calendar.pk)
    close()
  } catch (error) {
    formErrors.value = error.response?.data || {}
  } finally {
    working.value = false
  }
}
</script>
