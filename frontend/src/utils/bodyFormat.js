// Conversions of a message body between plain text and HTML, when the
// format of the editor changes. The HTML to text one follows
// html2plaintext (modoboa/webmail/lib/utils.py), used for the text part of
// the messages sent.

// Elements starting on a new line
const LINE_TAGS = new Set([
  'address',
  'article',
  'aside',
  'dd',
  'div',
  'dl',
  'dt',
  'figcaption',
  'figure',
  'footer',
  'form',
  'header',
  'li',
  'main',
  'nav',
  'ol',
  'section',
  'table',
  'tr',
  'ul',
])
// Elements separated from the surrounding text by a blank line
const PARAGRAPH_TAGS = new Set([
  'blockquote',
  'h1',
  'h2',
  'h3',
  'h4',
  'h5',
  'h6',
  'hr',
  'p',
  'pre',
])
// Elements whose content is never displayed
const HIDDEN_TAGS = new Set(['head', 'script', 'style', 'template', 'title'])

const escapeHtml = (text) =>
  text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')

// Lay out the text of an HTML document line by line
class PlainTextWriter {
  constructor() {
    this.lines = []
    this.current = ''
    this.quoteDepth = 0
    // Quote depth of the blank line to write before the next text
    this.pendingBlank = null
  }

  prefix(depth) {
    return '> '.repeat(depth)
  }

  write(text, preformatted = false) {
    if (!preformatted) {
      // HTML whitespace: a non-breaking space is never collapsed
      text = text.replace(/[ \t\n\r\f]+/g, ' ')
      if (!this.current || this.current.endsWith(' ')) {
        text = text.replace(/^ +/, '')
      }
      text = text.replace(/\u00a0/g, ' ')
    }
    text.split('\n').forEach((chunk, pos) => {
      if (pos) {
        this.endLine(true)
      }
      if (!chunk) {
        return
      }
      if (!this.current && this.pendingBlank !== null) {
        if (this.lines.length) {
          const depth = Math.min(this.pendingBlank, this.quoteDepth)
          this.lines.push(this.prefix(depth).trimEnd())
        }
        this.pendingBlank = null
      }
      this.current += chunk
    })
  }

  endLine(force = false) {
    if (!this.current && !force) {
      return
    }
    const line = this.prefix(this.quoteDepth) + this.current.trimEnd()
    this.lines.push(line.trimEnd())
    this.current = ''
  }

  endParagraph() {
    this.endLine()
    if (this.pendingBlank === null || this.pendingBlank > this.quoteDepth) {
      this.pendingBlank = this.quoteDepth
    }
  }

  // An empty paragraph of the editor: a line left blank on purpose
  blankLine() {
    this.endParagraph()
    this.lines.push(this.prefix(this.quoteDepth).trimEnd())
  }

  text() {
    this.endLine()
    return this.lines.join('\n').replace(/^\n+|\n+$/g, '')
  }
}

// Tell how an element is separated from the text around it
const blockKind = (element, tag) => {
  if (
    (tag === 'div' || tag === 'p') &&
    element.parentElement?.tagName.toLowerCase() === 'li'
  ) {
    // The editor puts the content of list items into paragraphs: it must
    // stay on the line of the item marker
    return 'item'
  }
  if (PARAGRAPH_TAGS.has(tag)) {
    return 'paragraph'
  }
  if (LINE_TAGS.has(tag)) {
    return 'line'
  }
  return null
}

const isEmptyParagraph = (element) =>
  element.tagName.toLowerCase() === 'p' &&
  !element.textContent.trim() &&
  !element.querySelector('img')

const walk = (node, writer, state) => {
  for (const child of node.childNodes) {
    if (child.nodeType === Node.TEXT_NODE) {
      writer.write(child.data, state.preformatted > 0)
      continue
    }
    if (child.nodeType !== Node.ELEMENT_NODE) {
      continue
    }
    const tag = child.tagName.toLowerCase()
    if (HIDDEN_TAGS.has(tag)) {
      continue
    }
    const kind = blockKind(child, tag)
    if (kind !== 'item' && isEmptyParagraph(child)) {
      writer.blankLine()
      continue
    }
    if (kind === 'paragraph') {
      writer.endParagraph()
    } else if (kind === 'line') {
      writer.endLine()
    } else if (
      kind === 'item' &&
      (child.previousElementSibling || child.previousSibling?.data?.trim())
    ) {
      // Not the first content of the item
      writer.endLine()
    }
    if (tag === 'blockquote') {
      writer.quoteDepth++
    } else if (tag === 'pre') {
      state.preformatted++
    } else if (tag === 'br') {
      writer.endLine(true)
    } else if (tag === 'hr') {
      writer.write('----')
    } else if (tag === 'img' && child.getAttribute('alt')) {
      writer.write(child.getAttribute('alt'))
    } else if (tag === 'ol' || tag === 'ul') {
      state.lists.push(tag === 'ol' ? 0 : null)
    } else if (tag === 'li') {
      const indent = '  '.repeat(Math.max(state.lists.length - 1, 0))
      const last = state.lists.length - 1
      if (last >= 0 && state.lists[last] !== null) {
        state.lists[last]++
        writer.write(`${indent}${state.lists[last]}. `, true)
      } else {
        writer.write(`${indent}- `, true)
      }
    }
    walk(child, writer, state)
    if (tag === 'a') {
      const href = child.getAttribute('href') || ''
      const label = child.textContent.trim()
      if (
        href &&
        !href.startsWith('#') &&
        !href.startsWith('javascript:') &&
        href !== label &&
        href !== `mailto:${label}`
      ) {
        writer.write(` <${href}>`)
      }
    } else if (tag === 'td' || tag === 'th') {
      writer.write(' ')
    } else if (tag === 'ol' || tag === 'ul') {
      state.lists.pop()
    }
    if (kind === 'paragraph') {
      writer.endParagraph()
    } else if (kind === 'line' || kind === 'item') {
      writer.endLine()
    }
    if (tag === 'blockquote') {
      writer.quoteDepth--
    } else if (tag === 'pre') {
      state.preformatted--
    }
  }
}

// HTML -> plain text: paragraphs, line breaks, lists and quotes ("> "
// prefix) are kept, the formatting is lost
export function htmlToPlain(html) {
  if (!html || !html.trim()) {
    return ''
  }
  const doc = new DOMParser().parseFromString(html, 'text/html')
  const writer = new PlainTextWriter()
  walk(doc.body, writer, { lists: [], preformatted: 0 })
  return writer.text()
}

// Plain text -> HTML: blank lines separate paragraphs, line breaks are kept
// and quoted lines (">" prefix) go into blockquotes
export function plainToHtml(text) {
  if (!text) {
    return ''
  }
  let html = ''
  let depth = 0
  let paragraph = []
  const flush = () => {
    if (paragraph.length) {
      html += `<p>${paragraph.join('<br>')}</p>`
      paragraph = []
    }
  }
  for (const line of text.replace(/\r\n?/g, '\n').split('\n')) {
    const quote = line.match(/^(?:> ?)+/)?.[0] || ''
    const lineDepth = (quote.match(/>/g) || []).length
    const content = line.slice(quote.length)
    if (lineDepth !== depth) {
      flush()
      html +=
        lineDepth > depth
          ? '<blockquote>'.repeat(lineDepth - depth)
          : '</blockquote>'.repeat(depth - lineDepth)
      depth = lineDepth
    }
    if (!content.trim()) {
      flush()
      continue
    }
    // Keep the indentation, that HTML would collapse
    paragraph.push(
      escapeHtml(content).replace(/^ +/, (spaces) =>
        '&nbsp;'.repeat(spaces.length)
      )
    )
  }
  flush()
  html += '</blockquote>'.repeat(depth)
  return html
}

// Convert a body from a format (plain or html) to another
export function convertBody(body, from, to) {
  if (!body || from === to) {
    return body
  }
  return to === 'html' ? plainToHtml(body) : htmlToPlain(body)
}
