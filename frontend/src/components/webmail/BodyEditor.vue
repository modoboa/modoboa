<template>
  <HtmlEditor
    v-if="format === 'html'"
    v-model="model"
    class="d-flex flex-column flex-grow-1 mt-4"
  >
    <template #append-toolbar>
      <v-btn
        class="mr-2"
        text="HTML"
        size="small"
        color="primary"
        variant="flat"
        :loading="converting"
        :title="$gettext('Switch to plain text')"
        @click="toggleFormat"
      />
    </template>
  </HtmlEditor>
  <template v-else>
    <div class="mt-8">
      <v-btn
        class="mr-2"
        text="HTML"
        size="small"
        color="grey-lighten-3"
        variant="flat"
        :loading="converting"
        :title="$gettext('Switch to HTML')"
        @click="toggleFormat"
      />
    </div>
    <v-textarea v-model="model" class="border-sm" />
  </template>
  <ConfirmDialog ref="confirmDialog" />
</template>

<script setup>
import { ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import HtmlEditor from '@/components/tools/HtmlEditor'
import api from '@/api/webmail'

const { $gettext } = useGettext()

const model = defineModel({ type: String, default: '' })
// Format of the body (plain or html): the content is converted when it
// changes
const format = defineModel('format', { type: String, default: 'plain' })

const confirmDialog = ref()
const converting = ref(false)

// The conversion is made by the server: the text obtained is the one sent
// as the text part of HTML messages
const convert = async (target) => {
  converting.value = true
  try {
    const resp = await api.convertBody(model.value, format.value, target)
    return resp.data.body
  } finally {
    converting.value = false
  }
}

// An empty editor holds an empty paragraph
const isEmpty = () => !(model.value || '').replace(/<p><\/p>/g, '').trim()

const toggleFormat = async () => {
  const target = format.value === 'plain' ? 'html' : 'plain'
  if (target === 'plain' && !isEmpty()) {
    // Asked first: the content can't change between the conversion and the
    // answer
    const confirmed = await confirmDialog.value.open(
      $gettext('Switch to plain text'),
      $gettext(
        'The formatting of the message (bold, links, images...) will be lost. Continue?'
      ),
      { agreeLabel: $gettext('Continue') }
    )
    if (!confirmed) {
      return
    }
  }
  try {
    model.value = await convert(target)
  } catch {
    // Already displayed to the user by the API client
    return
  }
  format.value = target
}
</script>
