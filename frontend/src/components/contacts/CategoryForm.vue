<template>
  <v-card>
    <v-form ref="formRef" @submit.prevent="submit">
      <v-card-title>
        <span class="headline">{{ title }}</span>
      </v-card-title>
      <v-card-text>
        <v-text-field
          v-model="form.name"
          :label="$gettext('Name')"
          variant="outlined"
          density="compact"
          :rules="[rules.required]"
        />
      </v-card-text>
      <v-card-actions>
        <v-btn v-if="category" color="red" @click="deleteCategory">
          {{ $gettext('Delete') }}
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn :loading="working" @click="close">
          {{ $gettext('Close') }}
        </v-btn>
        <v-btn color="primary" type="submit" :loading="working">
          {{ submitLabel }}
        </v-btn>
      </v-card-actions>
    </v-form>
  </v-card>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import contactsApi from '@/api/contacts'
import rules from '@/plugins/rules'

const props = defineProps({
  category: {
    type: Object,
    default: null,
  },
})
const emit = defineEmits(['close', 'updated'])

const router = useRouter()
const { $gettext } = useGettext()
const { displayNotification } = useBusStore()

const form = ref({})
const formRef = ref()
const working = ref(false)

const title = computed(() => {
  return props.category ? $gettext('Edit category') : $gettext('Add category')
})
const submitLabel = computed(() => {
  return props.category ? $gettext('Update') : $gettext('Add')
})

function close() {
  form.value = {}
  emit('close')
}
async function submit() {
  const { valid } = await formRef.value.validate()
  if (!valid) {
    return
  }
  working.value = true
  try {
    if (props.category) {
      await contactsApi.updateCategory(props.category.pk, form.value)
    } else {
      await contactsApi.addCategory(form.value)
    }
    emit('updated')
    emit('close')
  } catch (err) {
    console.log(err)
  } finally {
    working.value = false
  }
}

function deleteCategory() {
  contactsApi.deleteCategory(props.category.pk).then(() => {
    close()
    emit('updated')
    displayNotification({ msg: $gettext('Category deleted') })
    router.push({ name: 'ContactList' })
  })
}

watch(
  () => props.category,
  (value) => {
    if (value) {
      form.value = JSON.parse(JSON.stringify(value))
    } else {
      form.value = {}
    }
  },
  { immediate: true }
)
</script>
