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
      <template v-else>
        <v-text-field
          v-model="search"
          prepend-inner-icon="mdi-magnify"
          :placeholder="$gettext('Filter folders')"
          class="mb-2"
          variant="solo-filled"
          single-line
          flat
          hide-details
          density="compact"
          clearable
        />
        <!-- Big hierarchies can hold thousands of folders: only the
             visible rows are rendered. -->
        <v-virtual-scroll
          :items="rows"
          item-key="name"
          :item-height="ROW_HEIGHT"
          max-height="50vh"
        >
          <template #default="{ item }">
            <div
              class="d-flex align-center"
              :style="{ paddingInlineStart: `${item.depth * INDENT}px` }"
            >
              <!-- Kept (hidden) on leaves so labels stay aligned -->
              <v-btn
                :class="{ 'expand-hidden': !item.hasChildren }"
                :disabled="!item.hasChildren"
                :icon="
                  collapsed.has(item.name) ? 'mdi-menu-right' : 'mdi-menu-down'
                "
                :aria-label="
                  collapsed.has(item.name)
                    ? $gettext('Expand')
                    : $gettext('Collapse')
                "
                variant="text"
                size="small"
                density="comfortable"
                @click="toggleCollapsed(item.name)"
              />
              <v-checkbox
                :model-value="selected.has(item.name)"
                :label="item.label"
                :title="item.name"
                class="subscription-checkbox"
                density="compact"
                hide-details
                @update:model-value="(value) => setSelected(item.name, value)"
              />
            </div>
          </template>
        </v-virtual-scroll>
        <p v-if="!rows.length" class="text-body-2 text-medium-emphasis py-2">
          {{ $gettext('No folder found') }}
        </p>
      </template>
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
import { computed, onMounted, ref, shallowRef, triggerRef } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import api from '@/api/webmail'

const ROW_HEIGHT = 40
const INDENT = 24

const emit = defineEmits(['close', 'updated'])

const { $gettext } = useGettext()
const { displayNotification } = useBusStore()

const loading = ref(true)
const saving = ref(false)
const search = ref('')
// Folders in hierarchical order (a folder comes right before its
// descendants), see buildNodes().
const nodes = shallowRef([])
// Folders initially subscribed, used to compute the diff on apply.
const initial = new Set()
// Currently checked folders. Sets are mutated in place then triggered:
// copying them on every click would be costly with big hierarchies.
const selected = shallowRef(new Set())
// Folders whose children are hidden (everything is expanded by default).
const collapsed = shallowRef(new Set())

/**
 * Turn the flat list returned by the API (sorted on path components)
 * into display nodes. A folder is attached to its closest listed
 * ancestor; the label keeps the path components in between, so a folder
 * whose parent is not listed is still identifiable.
 */
function buildNodes(mailboxes, delimiter) {
  const byName = new Map()
  const result = []
  for (const mailbox of mailboxes) {
    const parts = mailbox.name.split(delimiter)
    let parent = null
    let index = parts.length - 1
    for (; index > 0; index--) {
      parent = byName.get(parts.slice(0, index).join(delimiter))
      if (parent) {
        break
      }
    }
    const node = {
      name: mailbox.name,
      label: parts.slice(index).join(delimiter),
      depth: parent ? parent.depth + 1 : 0,
      hasChildren: false,
    }
    if (parent) {
      parent.hasChildren = true
    }
    byName.set(node.name, node)
    result.push(node)
  }
  return result
}

const rows = computed(() => {
  const pattern = search.value?.trim().toLowerCase()
  if (pattern) {
    // Matching folders are listed flat, with their full path
    return nodes.value
      .filter((node) => node.name.toLowerCase().includes(pattern))
      .map((node) => ({
        name: node.name,
        label: node.name,
        depth: 0,
        hasChildren: false,
      }))
  }
  // Descendants follow their ancestor: skip the rows deeper than the
  // last collapsed folder.
  const result = []
  let hiddenBelow = null
  for (const node of nodes.value) {
    if (hiddenBelow !== null) {
      if (node.depth > hiddenBelow) {
        continue
      }
      hiddenBelow = null
    }
    result.push(node)
    if (node.hasChildren && collapsed.value.has(node.name)) {
      hiddenBelow = node.depth
    }
  }
  return result
})

function toggleCollapsed(name) {
  if (!collapsed.value.delete(name)) {
    collapsed.value.add(name)
  }
  triggerRef(collapsed)
}

function setSelected(name, value) {
  if (value) {
    selected.value.add(name)
  } else {
    selected.value.delete(name)
  }
  triggerRef(selected)
}

async function apply() {
  const changes = nodes.value
    .filter((node) => selected.value.has(node.name) !== initial.has(node.name))
    .map((node) => ({
      name: node.name,
      subscribed: selected.value.has(node.name),
    }))
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
    for (const mailbox of resp.data.mailboxes) {
      if (mailbox.subscribed) {
        initial.add(mailbox.name)
      }
    }
    selected.value = new Set(initial)
    nodes.value = buildNodes(resp.data.mailboxes, resp.data.hdelimiter)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.expand-hidden {
  visibility: hidden;
}

.subscription-checkbox {
  min-width: 0;
}

.subscription-checkbox :deep(.v-label) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
