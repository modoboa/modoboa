import { defineStore } from 'pinia'
import { ref } from 'vue'

const MAX_CACHED_CONTENTS = 20

export const useWebmailStore = defineStore('webmail', () => {
  const selection = ref([])
  const listingKey = ref(0)
  // How the messages list is displayed: one by one ('flat') or grouped
  // into conversations ('threaded'). Initialized from the user
  // preferences the first time a listing is displayed.
  const listingMode = ref('flat')
  const listingModeLoaded = ref(false)
  // Names of the special folders (draft, junk, trash...) as configured in
  // the user preferences, indexed by type. Filled from the mailboxes list,
  // whose entries carry that type.
  const specialFolders = ref({})
  // The last listing displayed, with what it was asked for: coming back
  // from a message shows it at once instead of requesting it again
  const lastListing = ref(null)
  // The webmail preferences, read once per session
  const preferences = ref(null)
  // Unseen counters received along the listings, by mailbox name
  const unseenCounters = ref({})
  // Contents of the messages already opened, by mailbox, id and display
  // options. A message never changes for a given id; only the most
  // recent ones are kept.
  const contents = new Map()

  const $reset = async () => {
    selection.value = []
    listingKey.value = 0
    listingMode.value = 'flat'
    listingModeLoaded.value = false
    specialFolders.value = {}
    lastListing.value = null
    preferences.value = null
    unseenCounters.value = {}
    contents.clear()
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

  function setListingMode(mode) {
    listingMode.value = mode === 'threaded' ? 'threaded' : 'flat'
    listingModeLoaded.value = true
  }

  function setUnseen(mailbox, counter) {
    if (Number.isInteger(counter)) {
      unseenCounters.value[mailbox] = counter
    }
  }

  const contentKey = (mailbox, mailid, options) =>
    JSON.stringify([mailbox, String(mailid), options])

  function getContent(mailbox, mailid, options) {
    const key = contentKey(mailbox, mailid, options)
    const content = contents.get(key)
    if (content !== undefined) {
      // Most recently used last
      contents.delete(key)
      contents.set(key, content)
    }
    return content
  }

  function setContent(mailbox, mailid, options, content) {
    contents.set(contentKey(mailbox, mailid, options), content)
    if (contents.size > MAX_CACHED_CONTENTS) {
      contents.delete(contents.keys().next().value)
    }
  }

  // The listing kept for the given mailbox, if any
  function listingOf(mailbox) {
    const listing = lastListing.value
    return listing?.mailbox === mailbox && listing.data.results ? listing : null
  }

  // Messages leave the listing as soon as they are deleted or moved,
  // without waiting for the listing to be requested again
  function removeFromListing(mailbox, ids) {
    const listing = listingOf(mailbox)
    if (!listing) {
      return
    }
    const removed = new Set(ids.map(String))
    listing.data.results = listing.threaded
      ? listing.data.results.filter(
          (thread) => !thread.uids.every((uid) => removed.has(String(uid)))
        )
      : listing.data.results.filter(
          (email) => !removed.has(String(email.imapid))
        )
  }

  // Same thing for flags ('read', 'unread', 'flagged' or 'unflagged')
  function flagInListing(mailbox, ids, status) {
    const listing = listingOf(mailbox)
    if (!listing) {
      return
    }
    const flagged = new Set(ids.map(String))
    for (const item of listing.data.results) {
      const uids = listing.threaded ? item.uids : [item.imapid]
      if (!uids.some((uid) => flagged.has(String(uid)))) {
        continue
      }
      if (status === 'flagged' || status === 'unflagged') {
        item.flagged = status === 'flagged'
      } else if (listing.threaded) {
        // Which messages of the thread were unread is unknown: only
        // what is certain is displayed, the next listing tells the rest
        const matched = uids.filter((uid) => flagged.has(String(uid))).length
        if (status === 'unread') {
          item.unseen_count = Math.max(item.unseen_count, matched)
        } else if (matched === uids.length) {
          item.unseen_count = 0
        }
      } else {
        item.style = status === 'read' ? undefined : 'unseen'
      }
    }
  }

  // The preferences changed: read them again, and the listing they shape
  function forgetPreferences() {
    preferences.value = null
    listingModeLoaded.value = false
    lastListing.value = null
  }

  // Opening a message marks it as read: one that is unread again must be
  // requested, not taken from the cache
  function forgetContent(mailbox, mailid) {
    for (const key of [...contents.keys()]) {
      const [cachedMailbox, cachedId] = JSON.parse(key)
      if (cachedMailbox === mailbox && cachedId === String(mailid)) {
        contents.delete(key)
      }
    }
  }

  return {
    selection,
    listingKey,
    listingMode,
    listingModeLoaded,
    setListingMode,
    specialFolders,
    setMailboxes,
    isFolder,
    lastListing,
    preferences,
    unseenCounters,
    setUnseen,
    getContent,
    setContent,
    forgetContent,
    removeFromListing,
    flagInListing,
    forgetPreferences,
    $reset,
  }
})
