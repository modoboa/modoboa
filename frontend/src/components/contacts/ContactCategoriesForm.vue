<template>
  <v-card>
    <v-form ref="formRef" @submit.prevent="submit">
      <v-card-title>
        <span class="headline">{{ $gettext('Categories') }}</span>
      </v-card-title>
      <v-card-text>
        <v-checkbox
          v-for="category in categories"
          :key="category.pk"
          v-model="selectedCategories"
          :label="category.name"
          hide-details
          :value="category.pk"
          color="primary"
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn :loading="working" @click="close">
          {{ $gettext('Close') }}
        </v-btn>
        <v-btn color="primary" type="submit" :loading="working">
          {{ $gettext('Update') }}
        </v-btn>
      </v-card-actions>
    </v-form>
  </v-card>
</template>

<script setup>
import { ref, watch } from 'vue'
import contactsApi from '@/api/contacts'

const props = defineProps({
  contact: {
    type: Object,
    default: null,
  },
})
const emit = defineEmits(['close'])

const categories = ref([])
const selectedCategories = ref([])
const working = ref(false)

function close() {
  emit('close', 'updated')
}

async function submit() {
  const data = { categories: selectedCategories.value }
  working.value = true
  try {
    await contactsApi.updateContact(props.contact.pk, data)
    emit('updated')
    close()
  } finally {
    working.value = false
  }
}

watch(
  () => props.contact,
  (value) => {
    if (value) {
      selectedCategories.value = value.categories
    } else {
      selectedCategories.value = []
    }
  },
  { immediate: true }
)

contactsApi.getCategories().then((resp) => {
  categories.value = resp.data
})
</script>
