import { createHash } from 'node:crypto'
import { describe, expect, it } from 'vitest'
import {
  SCROLL_SCRIPT,
  SCROLL_SCRIPT_HASH,
  buildEmailDocument,
} from './emailFrame'

describe('buildEmailDocument', () => {
  it('pins the CSP hash to the scroll script', () => {
    // If this fails, SCROLL_SCRIPT changed: update SCROLL_SCRIPT_HASH, or
    // the browser silently blocks the script and the progress bar dies.
    const digest = createHash('sha256').update(SCROLL_SCRIPT).digest('base64')
    expect(SCROLL_SCRIPT_HASH).toBe(`sha256-${digest}`)
  })

  it('blocks scripts other than the scroll one', () => {
    const doc = buildEmailDocument('<p>hi</p>')
    expect(doc).toContain(`script-src '${SCROLL_SCRIPT_HASH}'`)
    expect(doc).not.toContain("'unsafe-inline' 'unsafe-eval'")
    expect(doc).toContain("default-src 'none'")
  })

  it('only loads remote content when links are enabled', () => {
    expect(buildEmailDocument('x')).toContain('img-src data:;')
    expect(buildEmailDocument('x', { enableLinks: true })).toContain(
      'img-src data: https: http:;'
    )
  })

  it('returns an empty document without a body', () => {
    expect(buildEmailDocument('')).toBe('')
  })
})
