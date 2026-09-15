// Turn the body of an API error response into a message a user can read.

// Error pages from a reverse proxy or a crashed server are HTML documents,
// not messages.
const HTML_DOCUMENT = /^\s*</

const MAX_LENGTH = 300

// Keys holding a global message: Modoboa exceptions use "error", Django
// REST framework uses "detail" (404, 403...) and "non_field_errors".
const MESSAGE_KEYS = ['error', 'detail', 'non_field_errors']

function collectMessages(value) {
  if (value === null || value === undefined) {
    return []
  }
  if (typeof value === 'string') {
    const message = value.trim()
    return message && !HTML_DOCUMENT.test(message) ? [message] : []
  }
  if (Array.isArray(value)) {
    return value.flatMap(collectMessages)
  }
  if (typeof value === 'object') {
    for (const key of MESSAGE_KEYS) {
      if (key in value) {
        return collectMessages(value[key])
      }
    }
    // Validation errors: { field: [messages] }
    return Object.entries(value).flatMap(([field, messages]) =>
      collectMessages(messages).map((message) => `${field}: ${message}`)
    )
  }
  return [String(value)]
}

/**
 * Return a readable message for an API error response body, or null when
 * it holds nothing a user could read (empty body, HTML page...).
 */
export function getErrorMessage(data) {
  const message = collectMessages(data).join('; ')
  if (!message) {
    return null
  }
  if (message.length > MAX_LENGTH) {
    return `${message.slice(0, MAX_LENGTH - 1)}…`
  }
  return message
}
