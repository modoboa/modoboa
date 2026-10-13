import { computed, toValue } from 'vue'
import { useAuthStore, useWebmailStore } from '@/stores'

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

/**
 * A recipient as given to the API: "Name" <address> when the name is known.
 */
export function formatRecipient({ name, address }) {
  if (!name) {
    return address
  }
  return `"${name.replace(/(["\\])/g, '\\$1')}" <${address}>`
}

/**
 * A recipient without the quotes of its name: John Doe <john@example.com>
 */
export function displayRecipient(value) {
  return value.replace(/^"(.*)"(\s*<)/, '$1$2').replace(/\\(["\\])/g, '$1')
}

/**
 * The address of a recipient: "Name" <address>, Name <address> or address.
 */
export function getRecipientAddress(value) {
  const match = value.match(/<([^<>]*)>\s*$/)
  return (match ? match[1] : value).trim()
}

// The server checks the addresses: this only catches typing mistakes
export function isValidRecipient(value) {
  return /^[^\s@<>",;]+@[^\s@<>",;]+$/.test(getRecipientAddress(value))
}

/**
 * Split a list of recipients on commas, semicolons and line breaks, except
 * within a quoted name ("Doe, John") or an address between angle brackets.
 */
export function splitRecipients(value) {
  const result = []
  let current = ''
  let quoted = false
  let bracketed = false
  for (let i = 0; i < value.length; i++) {
    const char = value[i]
    if (quoted && char === '\\') {
      current += char + (value[i + 1] || '')
      i++
      continue
    }
    if (char === '"' && !bracketed) {
      quoted = !quoted
    } else if (char === '<' && !quoted) {
      bracketed = true
    } else if (char === '>' && !quoted) {
      bracketed = false
    } else if (!quoted && !bracketed && /[,;\r\n]/.test(char)) {
      result.push(current)
      current = ''
      continue
    }
    current += char
  }
  result.push(current)
  return result.map((item) => item.trim()).filter(Boolean)
}

/**
 * Keep the first recipient of each address.
 */
export function uniqueRecipients(recipients) {
  const seen = new Set()
  return recipients.filter((value) => {
    const address = getRecipientAddress(value).toLowerCase()
    if (seen.has(address)) {
      return false
    }
    seen.add(address)
    return true
  })
}

const RECENT_RECIPIENTS_MAX = 50

/**
 * The recipients the user wrote to lately, most recent first.
 *
 * They are kept in the browser, per user.
 */
export function useRecentRecipients() {
  const authStore = useAuthStore()
  const key = `webmail.recentRecipients.${authStore.authUser.username}`

  const load = () => {
    try {
      return JSON.parse(localStorage.getItem(key)) || []
    } catch {
      return []
    }
  }

  const remember = (recipients) => {
    const list = uniqueRecipients([...recipients, ...load()])
    try {
      localStorage.setItem(
        key,
        JSON.stringify(list.slice(0, RECENT_RECIPIENTS_MAX))
      )
    } catch {
      // Storage unavailable (private browsing...): nothing is remembered
    }
  }

  const search = (text) => {
    const value = text.toLowerCase()
    return load().filter((recipient) =>
      displayRecipient(recipient).toLowerCase().includes(value)
    )
  }

  return { remember, search }
}
