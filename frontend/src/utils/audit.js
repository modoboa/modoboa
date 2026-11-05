// Longer lists are summarized: the full list is in the message (on hover)
const MAX_LIST_ITEMS = 3

function formatValue(value) {
  if (!Array.isArray(value)) {
    return value
  }
  const shown = value.slice(0, MAX_LIST_ITEMS).join(', ')
  const hidden = value.length - MAX_LIST_ITEMS
  return hidden > 0 ? `${shown} +${hidden}` : shown
}

/**
 * One-line summary of what an audit entry is about: the object name, then
 * the event details (e.g. the names of the modified parameters).
 */
export function getAuditDetails(log) {
  const details = Object.values(log.extra || {}).map(formatValue)
  return [log.object_repr, ...details].filter(Boolean).join(' · ')
}
