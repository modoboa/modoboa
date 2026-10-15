import { beforeEach, describe, expect, it } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useWebmailStore } from './webmail.store'

const page = (results, count, next_page) => ({ results, count, next_page })
const row = (id) => ({ imapid: String(id), subject: `s${id}`, style: '' })

describe('webmail.store listing', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('accumulates pages in order', () => {
    const store = useWebmailStore()
    store.resetListing('INBOX')
    store.appendPage(page([row(3), row(2)], 5, 2))
    store.appendPage(page([row(1)], 5, null))
    expect(store.emails.map((e) => e.imapid)).toEqual(['3', '2', '1'])
    expect(store.emailCount).toBe(5)
    expect(store.nextPage).toBe(null)
  })

  it('dedupes by imapid across overlapping pages', () => {
    const store = useWebmailStore()
    store.resetListing('INBOX')
    store.appendPage(page([row(3), row(2)], 4, 2))
    // A message was deleted server-side, so page 2 repeats uid 2.
    store.appendPage(page([row(2), row(1)], 4, null))
    expect(store.emails.map((e) => e.imapid)).toEqual(['3', '2', '1'])
  })

  it('resetListing clears rows, selection and paging', () => {
    const store = useWebmailStore()
    store.selection = ['1', '2']
    store.appendPage(page([row(1)], 1, null))
    store.resetListing('Sent', 'foo')
    expect(store.emails).toEqual([])
    expect(store.emailCount).toBe(0)
    expect(store.nextPage).toBe(1)
    expect(store.selection).toEqual([])
    expect(store.listParams).toEqual({
      mailbox: 'Sent',
      search: 'foo',
      mode: null,
    })
  })

  it('a listing loaded in another mode is not fresh', () => {
    const store = useWebmailStore()
    store.listingMode = 'flat'
    store.resetListing('INBOX')
    store.appendPage(page([row(1)], 1, null))
    expect(store.isListingFresh('INBOX')).toBe(true)
    store.listingMode = 'threaded'
    expect(store.isListingFresh('INBOX')).toBe(false)
  })

  it('selection expands to every message of the selected conversations', () => {
    const store = useWebmailStore()
    store.appendPage(
      page(
        [
          { ...row(3), thread: { uids: ['1', '2', '3'] } },
          row(5),
        ],
        2,
        null
      )
    )
    store.selection = ['3', '5']
    expect(store.selectionUids).toEqual(['1', '2', '3', '5'])
    expect(store.uidsOf(store.emails[1])).toEqual([store.emails[1].imapid])
  })

  it('isListingFresh only for matching params with rows and within TTL', () => {
    const store = useWebmailStore()
    store.resetListing('INBOX', '')
    expect(store.isListingFresh('INBOX', '')).toBe(false) // no rows yet
    store.appendPage(page([row(1)], 1, null))
    expect(store.isListingFresh('INBOX', '')).toBe(true)
    expect(store.isListingFresh('INBOX', 'q')).toBe(false) // search differs
    expect(store.isListingFresh('Sent', '')).toBe(false) // mailbox differs
    store.listLoadedAt = Date.now() - 6 * 60 * 1000 // older than TTL
    expect(store.isListingFresh('INBOX', '')).toBe(false)
  })

  it('removeEmails drops rows and decrements count', () => {
    const store = useWebmailStore()
    store.resetListing('INBOX')
    store.appendPage(page([row(3), row(2), row(1)], 3, null))
    store.removeEmails(['2'])
    expect(store.emails.map((e) => e.imapid)).toEqual(['3', '1'])
    expect(store.emailCount).toBe(2)
  })

  it('restoreEmails reinserts a row at its index', () => {
    const store = useWebmailStore()
    store.resetListing('INBOX')
    store.appendPage(page([row(3), row(2), row(1)], 3, null))
    const removed = store.emails[1]
    store.removeEmails(['2'])
    store.restoreEmails([removed], 1)
    expect(store.emails.map((e) => e.imapid)).toEqual(['3', '2', '1'])
    expect(store.emailCount).toBe(3)
  })

  it('patchEmail mutates a row in place', () => {
    const store = useWebmailStore()
    store.resetListing('INBOX')
    store.appendPage(page([{ imapid: '1', style: 'unseen' }], 1, null))
    store.patchEmail('1', { style: '' })
    expect(store.emails[0].style).toBe('')
  })
})
