import { defineStore } from 'pinia'
import { ref } from 'vue'

// Listing pages are considered fresh for this long; on remount within the
// window (e.g. back from the reading view on mobile) we restore the cached
// pages + scroll position instead of refetching from page 1.
const LISTING_TTL_MS = 5 * 60 * 1000

export const useWebmailStore = defineStore('webmail', () => {
  const selection = ref([])
  const listingKey = ref(0)
  // Names of the special folders (draft, junk, trash...) as configured in
  // the user preferences, indexed by type. Filled from the mailboxes list,
  // whose entries carry that type.
  const specialFolders = ref({})

  // ----- infinite-scroll listing state -----
  const emails = ref([]) // accumulated rows across pages
  const emailCount = ref(0) // total server-side count for current params
  const nextPage = ref(1) // null once exhausted
  const listParams = ref({ mailbox: null, search: '' })
  const listScrollTop = ref(0)
  const listLoadedAt = ref(0)

  const resetListing = (mailbox, search = '') => {
    emails.value = []
    emailCount.value = 0
    nextPage.value = 1
    listParams.value = { mailbox, search }
    listScrollTop.value = 0
    listLoadedAt.value = 0
    selection.value = []
  }

  const appendPage = ({ results, count, next_page }) => {
    // Dedupe by imapid: rows shift server-side when messages are deleted
    // between page fetches, so the same UID can reappear on the next page.
    // Duplicates are the visible failure mode; a gap is acceptable and heals
    // on the next full refresh.
    const seen = new Set(emails.value.map((e) => e.imapid))
    for (const row of results || []) {
      if (!seen.has(row.imapid)) {
        emails.value.push(row)
        seen.add(row.imapid)
      }
    }
    emailCount.value = count ?? emails.value.length
    nextPage.value = next_page ?? null
    if (!listLoadedAt.value) {
      listLoadedAt.value = Date.now()
    }
  }

  const isListingFresh = (mailbox, search = '') =>
    listParams.value.mailbox === mailbox &&
    listParams.value.search === search &&
    emails.value.length > 0 &&
    Date.now() - listLoadedAt.value < LISTING_TTL_MS

  const removeEmails = (imapids) => {
    const set = new Set(imapids.map(String))
    emails.value = emails.value.filter((e) => !set.has(String(e.imapid)))
    if (emailCount.value > 0) {
      emailCount.value = Math.max(0, emailCount.value - set.size)
    }
  }

  const restoreEmails = (rows, index) => {
    const at = index == null ? emails.value.length : index
    emails.value.splice(at, 0, ...rows)
    emailCount.value += rows.length
  }

  const patchEmail = (imapid, patch) => {
    const row = emails.value.find((e) => String(e.imapid) === String(imapid))
    if (row) {
      Object.assign(row, patch)
    }
  }

  const $reset = async () => {
    selection.value = []
    listingKey.value = 0
    emails.value = []
    emailCount.value = 0
    nextPage.value = 1
    listParams.value = { mailbox: null, search: '' }
    listScrollTop.value = 0
    listLoadedAt.value = 0
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
    emails,
    emailCount,
    nextPage,
    listParams,
    listScrollTop,
    listLoadedAt,
    resetListing,
    appendPage,
    isListingFresh,
    removeEmails,
    restoreEmails,
    patchEmail,
    specialFolders,
    setMailboxes,
    isFolder,
    $reset,
  }
})
