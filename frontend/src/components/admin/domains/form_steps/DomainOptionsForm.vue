<template>
  <v-form ref="vFormRef">
    <v-switch
      v-model="createAdmin"
      :label="$gettext('Create a domain administrator')"
      color="primary"
      @update:model-value="updateCreateAdmin"
    />
    <v-text-field
      v-model="domain.domain_admin.username"
      :label="$gettext('Name')"
      :hint="$gettext('Name of the administrator')"
      persistent-hint
      variant="outlined"
      :disabled="!createAdmin"
      :suffix="`@${domain.name}`"
      :rules="[!createAdmin || rules.required]"
    />
    <AccountPasswordSubForm
      v-model="domain.domain_admin"
      :disabled="!createAdmin"
    />
    <v-switch
      v-model="domain.domain_admin.with_mailbox"
      :label="$gettext('With a mailbox')"
      :disabled="!createAdmin"
      :hint="$gettext('Create a mailbox for the administrator.')"
      persistent-hint
      color="primary"
    />
    <v-switch
      v-model="domain.domain_admin.with_aliases"
      :label="$gettext('Create aliases')"
      :disabled="!createAdmin"
      :hint="$gettext('Create standard aliases for the domain.')"
      persistent-hint
      color="primary"
    />
  </v-form>
</template>

<script setup lang="js">
import AccountPasswordSubForm from '@/components/admin/identities/form_steps/AccountPasswordSubForm.vue'
import { ref, computed } from 'vue'
import { useGettext } from 'vue3-gettext'
import rules from '@/plugins/rules.js'

const { $gettext } = useGettext()

const props = defineProps({ modelValue: { type: Object, default: null } })
const emit = defineEmits(['createAdmin'])

const vFormRef = ref()

const createAdmin = ref(false)

const domain = computed(() => props.modelValue)

function updateCreateAdmin(val) {
  emit('createAdmin', val)
}

defineExpose({ vFormRef })
</script>
