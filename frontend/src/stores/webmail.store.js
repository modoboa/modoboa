import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useWebmailStore = defineStore('webmail', () => {
  const selection = ref([])
  const listingKey = ref(0)
  // Names of the special folders (draft, junk, trash...) as configured in
  // the user preferences, indexed by type. Filled from the mailboxes list,
  // whose entries carry that type.
  const specialFolders = ref({})

  const $reset = async () => {
    selection.value = []
    listingKey.value = 0
    specialFolders.value = {}
  }

  function setMailboxes(mailboxes) {
    const folders = {}
    for (const mailbox of mailboxes || []) {
      if (mailbox.type && mailbox.type !== 'normal') {
        folders[mailbox.type] = mailbox.name
      }
    }
    specialFolders.value = folders
  }

  // Is the given mailbox the special folder of this type?
  function isFolder(type, name) {
    return !!name && specialFolders.value[type] === name
  }

  return {
    selection,
    listingKey,
    specialFolders,
    setMailboxes,
    isFolder,
    $reset,
  }
})
