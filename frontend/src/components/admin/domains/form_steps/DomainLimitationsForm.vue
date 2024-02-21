<template>
  <v-form ref="vFormRef">
    <v-text-field
      v-model="domain.quota"
      :label="$gettext('Quota')"
      :hint="
        $gettext(
          'Quota shared between mailboxes. Can be expressed in KB, MB (default) or GB. A value of 0 means no quota.'
        )
      "
      persistent-hint
      class="mb-4"
      variant="outlined"
      :rules="[rules.required]"
    />

    <v-text-field
      v-model="domain.default_mailbox_quota"
      :label="$gettext('Default mailbox quota')"
      :hint="
        $gettext(
          'Default quota applied to mailboxes. Can be expressed in KB, MB (default) or GB. A value of 0 means no quota.'
        )
      "
      persistent-hint
      class="mb-4"
      variant="outlined"
      :rules="[rules.required]"
    />
    <v-text-field
      v-model="domain.message_limit"
      :label="$gettext('Message sending limit')"
      :hint="
        $gettext(
          'Number of messages this domain can send per day. Leave empty for no limit.'
        )
      "
      persistent-hint
      variant="outlined"
      :rules="[rules.numericOrNull]"
    />
  </v-form>
</template>

<script setup lang="js">
import { computed, ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import rules from '@/plugins/rules.js'

const { $gettext } = useGettext()

const props = defineProps({ modelValue: { type: Object, default: null } })

const vFormRef = ref()

const domain = computed(() => props.modelValue)

defineExpose({ vFormRef })
</script>
