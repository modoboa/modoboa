<template>
  <v-card flat>
    <v-card-text>
      <label class="m-label">{{ $gettext('Recipient(s)') }}</label>
      <v-textarea
        v-model="form.recipients"
        :hint="
          $gettext('Indicate one or more recipients separated by a comma (,)')
        "
        persistent-hint
        rows="3"
        variant="outlined"
      />
      <v-checkbox
        v-model="form.keepcopies"
        :label="$gettext('Keep local copies')"
        :hint="
          $gettext('Forward messages and store copies into your local mailbox')
        "
        persistent-hint
      />
    </v-card-text>
    <v-card-actions class="pa-4">
      <v-btn color="success" variant="flat" :loading="loading" @click="submit">
        {{ $gettext('Update') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="js">
import { ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import accountApi from '@/api/account'
import { useBusStore } from '@/stores/bus.store'

const { $gettext } = useGettext()
const busStore = useBusStore()

const form = ref({})
const loading = ref(false)

function submit() {
  loading.value = true
  accountApi.setForward(form.value).then(() => {
    loading.value = false
    busStore.displayNotification({
      type: 'success',
      msg: $gettext('Forward updated'),
    })
  })
}

accountApi.getForward().then((resp) => {
  form.value = resp.data
})
</script>
