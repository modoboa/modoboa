<template>
  <v-card :title="$gettext('Tags')">
    <v-card-text>
      <v-list density="compact">
        <v-list-item
          v-for="tag in webmailStore.tags || []"
          :key="tag.pk"
          :title="tag.label"
          :active="editing?.pk === tag.pk"
        >
          <template #prepend>
            <v-icon icon="mdi-tag" :color="tag.color" />
          </template>
          <template #append>
            <v-btn
              icon="mdi-pencil-outline"
              variant="text"
              size="small"
              :title="$gettext('Edit')"
              @click="edit(tag)"
            />
            <v-btn
              icon="mdi-delete-outline"
              variant="text"
              size="small"
              color="error"
              :title="$gettext('Delete')"
              @click="remove(tag)"
            />
          </template>
        </v-list-item>
      </v-list>
      <v-form class="d-flex ga-2 align-start mt-4" @submit.prevent="submit">
        <v-text-field
          v-model="form.label"
          :label="$gettext('Name')"
          :error-messages="errors.label"
          maxlength="64"
          density="compact"
          variant="outlined"
        />
        <ColorField v-model="form.color" :error-messages="errors.color" />
      </v-form>
    </v-card-text>
    <v-card-actions>
      <v-btn v-if="editing" @click="reset">{{ $gettext('Cancel') }}</v-btn>
      <v-spacer />
      <v-btn @click="emit('close')">{{ $gettext('Close') }}</v-btn>
      <v-btn
        color="primary"
        variant="flat"
        :loading="working"
        :disabled="!form.label || !form.color"
        @click="submit"
      >
        {{ editing ? $gettext('Update') : $gettext('Add') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useBusStore, useWebmailStore } from '@/stores'
import ColorField from '@/components/tools/ColorField.vue'
import api from '@/api/webmail'

const emit = defineEmits(['close'])

const { $gettext } = useGettext()
const { displayNotification } = useBusStore()
const webmailStore = useWebmailStore()

const DEFAULT_COLOR = '#607d8b'
const editing = ref(null)
const form = ref({ label: '', color: DEFAULT_COLOR })
const errors = ref({})
const working = ref(false)

const reset = () => {
  editing.value = null
  form.value = { label: '', color: DEFAULT_COLOR }
  errors.value = {}
}

const edit = (tag) => {
  editing.value = tag
  form.value = { label: tag.label, color: tag.color }
  errors.value = {}
}

const submit = async () => {
  working.value = true
  try {
    if (editing.value) {
      await api.updateTag(editing.value.pk, form.value)
    } else {
      await api.createTag(form.value)
    }
    await webmailStore.loadTags(true)
    displayNotification({
      msg: editing.value ? $gettext('Tag updated') : $gettext('Tag created'),
    })
    reset()
  } catch (error) {
    // Field errors are displayed under the fields, others are notified
    const data = error.response?.data
    errors.value = data && !Array.isArray(data) ? data : {}
  } finally {
    working.value = false
  }
}

// The keyword stays on the messages: it shows again if a tag of the
// same name is created
const remove = async (tag) => {
  await api.deleteTag(tag.pk)
  if (editing.value?.pk === tag.pk) {
    reset()
  }
  await webmailStore.loadTags(true)
  displayNotification({ msg: $gettext('Tag deleted') })
}
</script>
