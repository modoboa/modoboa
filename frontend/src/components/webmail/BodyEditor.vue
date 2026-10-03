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
import { htmlToPlain, plainToHtml } from '@/utils/bodyFormat'

const { $gettext } = useGettext()

const model = defineModel({ type: String, default: '' })
// Format of the body (plain or html): the content is converted when it
// changes
const format = defineModel('format', { type: String, default: 'plain' })

const confirmDialog = ref()

const toggleFormat = async () => {
  if (format.value === 'plain') {
    model.value = plainToHtml(model.value)
    format.value = 'html'
    return
  }
  const text = htmlToPlain(model.value)
  if (text) {
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
  model.value = text
  format.value = 'plain'
}
</script>
