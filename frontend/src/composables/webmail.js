import { computed, toValue } from 'vue'
import { useWebmailStore } from '@/stores'

/**
 * Tell whether a mailbox is one of the user's special folders.
 *
 * The names of these folders are user preferences: they are recognized by
 * type, from the mailboxes list loaded by the webmail layout.
 *
 * @param {Ref<string>|Function|string} mailbox the mailbox name
 */
export function useSpecialFolders(mailbox) {
  const webmailStore = useWebmailStore()

  const isFolder = (type) =>
    computed(() => webmailStore.isFolder(type, toValue(mailbox)))

  return {
    isDraftsFolder: isFolder('draft'),
    isJunkFolder: isFolder('junk'),
    isTrashFolder: isFolder('trash'),
  }
}
