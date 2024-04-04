<template>
  <v-card
    :title="$gettext('Create a new filter set')"
  >
    <v-card-text>
      <v-form ref="formRef">
        <v-text-field
          v-model="form.name"
          :label="$gettext('Name')"
          variant="outlined"
          :rules="[rules.required]"
        />
        <v-switch
          :label="$gettext('Active')"
          v-model="form.active"
          color="primary"
          />
      </v-form>
    </v-card-text>
    <v-divider></v-divider>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn
        :text="$gettext('Cancel')"
        variant="plain"
        @click="close"
      ></v-btn>
      <v-btn
        color="primary"
        :text="$gettext('Create')"
        @click="submit"
      ></v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'
import { useBusStore } from '@/stores'
import { useGettext } from 'vue3-gettext'
import rules from '@/plugins/rules'
import accountApi from '@/api/account'

const { $gettext } = useGettext()
const emit = defineEmits(['close'])
const busStore = useBusStore()

const form = ref({})
const formRef = ref()
const working = ref(false)

function close() {
  formRef.value.reset()
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
    await accountApi.createFilterSet(form.value)
    busStore.displayNotification({ msg: $gettext('Filter set created') })
    close()
  } finally {
    working.value = false
  }
}
</script>
