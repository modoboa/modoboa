<template>
  <v-card flat>
    <v-card-text>
      <v-form ref="formRef" @submit.prevent="submit">
        <v-checkbox
          v-model="form.enabled"
          :label="$gettext('Enabled')"
          color="primary"
          hide-details
          class="mb-4"
        />
        <label class="m-label">{{ $gettext('Subject') }}</label>
        <v-text-field
          v-model="form.subject"
          variant="outlined"
          density="compact"
          :rules="[rules.required]"
        />
        <div class="mb-4">
          <label class="m-label">{{ $gettext('Content') }}</label>
          <v-textarea
            v-model="form.content"
            :hint="$gettext('The content of your answer. You can use the following variables, which will be automatically replaced by the appropriate value: %(name)s, %(fromdate)s, %(untildate)s')"
            persistent-hint
            variant="outlined"
            rows="3"
            density="compact"
            :rules="[rules.required]"
          />
        </div>
        <div class="mb-4">
          <label class="m-label">{{ $gettext('From') }}</label>
          <v-text-field
            v-model="form.fromdate"
            :hint="$gettext('Activate your auto reply from this date')"
            variant="outlined"
            persistent-hint
            type="datetime-local"
            density="compact"
          />
        </div>
        <div class="mb-4">
          <label class="m-label">{{ $gettext('Until') }}</label>
          <v-text-field
            v-model="form.untildate"
            :hint="$gettext('Activate your auto reply until this date')"
            variant="outlined"
            persistent-hint
            type="datetime-local"
            density="compact"
          />
        </div>
        <v-btn color="success" type="submit" :loading="loading">
          {{ $gettext('Update auto-reply') }}
        </v-btn>
      </v-form>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'
import { useBusStore } from '@/stores'
import { useGettext } from 'vue3-gettext'
import accountApi from '@/api/account'
import rules from '@/plugins/rules'

const busStore = useBusStore()
const { $gettext } = useGettext()

const form = ref({})
const formRef = ref()
const loading = ref(false)

async function submit() {
  const { valid } = await formRef.value.validate()
  if (!valid) {
    return
  }
  loading.value = true
  accountApi.setARMessage(form.value).then(() => {
    busStore.displayNotification({ msg: $gettext('Auto-reply message updated') })
    loading.value = false
  }).catch(() => {
    loading.value = false
  })
}

accountApi.getARMessage().then(resp => {
  form.value = resp.data
  if (form.value.fromdate) {
    form.value.fromdate = form.value.fromdate.slice(0, -4)
  }
  if (form.value.untildate) {
    form.value.untildate = form.value.untildate.slice(0, -4)
  }
})
</script>
