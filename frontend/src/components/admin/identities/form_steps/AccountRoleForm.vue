<template>
  <v-form ref="vFormRef">
    <v-row>
      <v-col cols="7">
        <ChoiceField
          v-model="account.role"
          :label="$gettext('Choose a role')"
          :choices="accountRoles"
          :choices-per-line="2"
        />
      </v-col>
      <v-col cols="5">
        <v-alert color="primary" class="mt-11 ml-4 rounded-lg">
          <h3 class="headline">{{ roleLabel }}</h3>
          <p class="mt-4">{{ roleHelp }}</p>
          <v-icon
            color="white"
            class="float-right"
            size="large"
            icon="mdi-help-circle-outline"
          />
        </v-alert>
      </v-col>
    </v-row>
  </v-form>
</template>

<script setup>
import ChoiceField from '@/components/tools/ChoiceField'
import { computed, ref } from 'vue'
import { useAuthStore } from '@/stores'
import { useGettext } from 'vue3-gettext'
import constants from '@/constants.json'

const authStore = useAuthStore()
const { $gettext } = useGettext()

const props = defineProps({
  modelValue: { type: Object, default: null },
})

const vFormRef = ref()

const account = computed(() => props.modelValue)

const authUser = computed(() => authStore.authUser)

const roleLabel = computed(() => {
  const role = accountRoles.value.find(
    (roleTarget) => roleTarget.value === account.value.role
  )
  return role !== undefined ? role.label : ''
})

const roleHelp = computed(() => {
  const role = accountRoles.value.find(
    (roleTarget) => roleTarget.value === account.value.role
  )
  return role !== undefined ? role.help : ''
})

const accountRoles = computed(() => {
  if (authUser.value.role === constants.SUPER_ADMIN) {
    return [
      ...simpleUserRole,
      ...domainAdminsRole,
      ...resellerRole,
      ...superAdminsRole,
    ]
  } else if (authUser.value.role === constants.DOMAIN_ADMIN) {
    return [...simpleUserRole]
  } else if (authUser.value.role === constants.RESELLER) {
    return [...domainAdminsRole, ...simpleUserRole]
  } else {
    return []
  }
})

const simpleUserRole = [
  {
    label: $gettext('Simple user'),
    value: constants.USER,
    help: $gettext(
      'A user with no privileges but with a mailbox. He will be allowed to use all end-user features: webmail, calendar, contacts, filters.'
    ),
  },
]

const domainAdminsRole = [
  {
    label: $gettext('Domain administrator'),
    value: constants.DOMAIN_ADMIN,
    help: $gettext(
      'A user with privileges on one or more domain. He will be allowed to administer mailboxes and he can also have a mailbox.'
    ),
  },
]
const resellerRole = [
  {
    label: $gettext('Reseller'),
    value: constants.RESELLER,
    help: $gettext(
      'An intermediate user who has the same privileges than a Domain administrator, plus the possibility to create domains and to assign resources.'
    ),
  },
]
const superAdminsRole = [
  {
    label: $gettext('Super administrator'),
    value: constants.SUPER_ADMIN,
    help: $gettext(
      "A user with all privileges, can do anything. By default, such a user does not have a mailbox so he can't access end-user features."
    ),
  },
]

defineExpose({ vFormRef, roleLabel })
</script>
