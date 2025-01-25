<template>
  <v-card>
    <v-form ref="formRef" @submit.prevent="submit">
      <v-card-title>
        <span class="headline">{{ title }}</span>
      </v-card-title>
      <v-card-text>
        <v-row no-gutters>
          <v-col cols="6">
            <v-text-field
              v-model="form.first_name"
              :label="$gettext('First name')"
              variant="outlined"
              prepend-icon="mdi-account"
              density="compact"
              :error-messages="formErrors.first_name"
            />
          </v-col>
          <v-col cols="6" class="pl-4">
            <v-text-field
              v-model="form.last_name"
              :label="$gettext('Last name')"
              variant="outlined"
              density="compact"
              :error-messages="formErrors.last_name"
            />
          </v-col>
          <v-col cols="12">
            <v-text-field
              v-model="form.display_name"
              :label="$gettext('Display name')"
              variant="outlined"
              prepend-icon="toto"
              density="compact"
              :error-messages="formErrors.display_name"
            />
          </v-col>
          <v-col cols="6">
            <v-text-field
              v-model="form.company"
              :label="$gettext('Company')"
              variant="outlined"
              prepend-icon="mdi-office-building"
              density="compact"
            />
          </v-col>
          <v-col cols="6" class="pl-4">
            <v-text-field
              v-model="form.position"
              :label="$gettext('Position')"
              variant="outlined"
              density="compact"
            />
          </v-col>
          <EmailField
            v-for="(email, index) in form.emails"
            :key="`email-${index}`"
            v-model="form.emails[index]"
            :index="index"
            @add="addEmailField"
            @delete="deleteEmailField"
          />
          <PhoneNumberField
            v-for="(phone, index) in form.phone_numbers"
            :key="`phone-${index}`"
            v-model="form.phone_numbers[index]"
            :index="index"
            @add="addPhoneNumberField"
            @delete="deletePhoneNumberField"
          />
          <template v-if="showExtraFields">
            <v-col cols="6">
              <v-text-field
                v-model="form.birth_date"
                :label="$gettext('Birth date')"
                type="date"
                prepend-icon="mdi-calendar"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="12">
              <v-textarea
                v-model="form.address"
                :label="$gettext('Address')"
                prepend-icon="mdi-location"
                variant="outlined"
                density="compact"
                rows="2"
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="form.zipcode"
                :label="$gettext('Zip code')"
                prepend-icon="toto"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="6" class="pl-4">
              <v-text-field
                v-model="form.city"
                :label="$gettext('City')"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="form.country"
                :label="$gettext('Country')"
                prepend-icon="toto"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="6" class="pl-4">
              <v-text-field
                v-model="form.state"
                :label="$gettext('State/Province')"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="12">
              <v-textarea
                v-model="form.note"
                :label="$gettext('Note')"
                prepend-icon="mdi-file"
                variant="outlined"
                density="compact"
                rows="2"
              />
            </v-col>
          </template>
        </v-row>
      </v-card-text>
      <v-card-actions>
        <v-btn v-if="!showExtraFields" @click="showExtraFields = true">
          {{ $gettext('More') }}
        </v-btn>
        <v-btn v-else @click="showExtraFields = false">
          {{ $gettext('Less') }}
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn :loading="working" @click="emit('close')">
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
import { useGettext } from 'vue3-gettext'
import contactsApi from '@/api/contacts'
import EmailField from './EmailField.vue'
import PhoneNumberField from './PhoneNumberField.vue'

const emit = defineEmits(['close', 'added', 'updated'])
const props = defineProps({
  contact: {
    type: Object,
    required: false,
  },
})

const { $gettext } = useGettext()

const form = ref(initialForm())
const showExtraFields = ref(false)
const formRef = ref()
const formErrors = ref({})
const working = ref(false)

const title = computed(() => {
  return props.contact ? $gettext('Edit contact') : $gettext('New contact')
})
const submitLabel = computed(() => {
  return props.contact ? $gettext('Update') : $gettext('Add')
})

function initialForm() {
  return {
    emails: [{}],
    phone_numbers: [{}],
  }
}

function addEmailField() {
  form.value.emails.push({})
}

function deleteEmailField(index) {
  form.value.emails.splice(index, 1)
}

function addPhoneNumberField() {
  form.value.phone_numbers.push({})
}

function deletePhoneNumberField(index) {
  form.value.phone_numbers.splice(index, 1)
}

async function submit() {
  const { valid } = await formRef.value.validate()
  if (!valid) {
    return
  }
  working.value = true
  const data = JSON.parse(JSON.stringify(form.value))
  if (!Object.keys(data.phone_numbers[0]).length) {
    data.phone_numbers.splice(0, 1)
  }
  try {
    let resp
    if (props.contact) {
      resp = await contactsApi.updateContact(props.contact.pk, data)
      emit('updated', resp.data)
    } else {
      resp = await contactsApi.createContact(data)
      emit('added', resp.data)
    }
    emit('close')
  } catch (err) {
    if (err.response?.status === 400) {
      formErrors.value = err.response.data
    }
  } finally {
    working.value = false
  }
}

watch(
  () => props.contact,
  (value) => {
    if (value) {
      form.value = JSON.parse(JSON.stringify(value))
      if (!form.value.phone_numbers.length) {
        form.value.phone_numbers = [{}]
      }
    } else {
      form.value = initialForm()
    }
  },
  { immediate: true }
)
</script>
