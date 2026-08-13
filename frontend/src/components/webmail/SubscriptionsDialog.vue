<template>
  <v-card :title="$gettext('Subscriptions')">
    <v-card-text>
      <p class="text-body-2 text-medium-emphasis mb-4">
        {{
          $gettext(
            'Check the folders you want to subscribe to. Only subscribed folders are displayed in the webmail.'
          )
        }}
      </p>
      <div v-if="loading" class="d-flex justify-center py-4">
        <v-progress-circular indeterminate color="primary" />
      </div>
      <v-treeview
        v-else
        v-model:selected="selected"
        :items="mailboxes"
        item-value="name"
        item-title="label"
        item-children="sub"
        select-strategy="independent"
        selectable
        open-all
        density="compact"
        fluid
        class="subscription-tree"
      />
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn
        :text="$gettext('Cancel')"
        variant="flat"
        :disabled="saving"
        @click="emit('close')"
      />
      <v-btn
        :text="$gettext('Apply')"
        variant="tonal"
        color="primary"
        :loading="saving"
        @click="apply"
      />
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import api from '@/api/webmail'

const emit = defineEmits(['close', 'updated'])

const { $gettext } = useGettext()
const { displayNotification } = useBusStore()

const loading = ref(true)
const saving = ref(false)
const mailboxes = ref([])
// Names of every folder, and the set initially subscribed, used to
// compute the diff on apply.
const allNames = ref([])
const initial = ref(new Set())
// Currently checked folders (bound to the treeview).
const selected = ref([])

function collect(nodes) {
  for (const node of nodes) {
    allNames.value.push(node.name)
    if (node.subscribed) {
      initial.value.add(node.name)
      selected.value.push(node.name)
    }
    if (node.sub && node.sub.length) {
      collect(node.sub)
    }
  }
}

async function apply() {
  const current = new Set(selected.value)
  const changes = allNames.value
    .filter((name) => current.has(name) !== initial.value.has(name))
    .map((name) => ({ name, subscribed: current.has(name) }))
  if (changes.length === 0) {
    emit('close')
    return
  }
  saving.value = true
  try {
    await api.updateSubscriptions(changes)
    displayNotification({ msg: $gettext('Subscriptions updated') })
    emit('updated')
    emit('close')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    const resp = await api.getSubscriptions()
    mailboxes.value = resp.data.mailboxes
    collect(mailboxes.value)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.subscription-tree {
  max-height: 50vh;
  overflow-y: auto;
}
</style>
