// Document rendered in the sandboxed iframe that displays a message body.
//
// The body is untrusted: the iframe has no `allow-same-origin`, so it runs in
// an opaque origin and can never reach the application, even if the
// server-side HTML cleaner is bypassed. The parent can't read that document
// either, so the reading-progress bar is fed by SCROLL_SCRIPT through
// postMessage. The CSP only lets that exact script run (by hash): any script
// shipped in the message stays blocked.

export const SCROLL_MESSAGE = 'modoboa-email-scroll'

export const SCROLL_SCRIPT =
  '(function(){' +
  'var d=document.scrollingElement||document.documentElement;' +
  "addEventListener('scroll',function(){" +
  'var m=d.scrollHeight-d.clientHeight;' +
  `parent.postMessage({type:'${SCROLL_MESSAGE}',value:m>0?d.scrollTop/m:0},'*')` +
  '},{passive:true})' +
  '})()'

// sha256 of SCROLL_SCRIPT, base64 (checked by emailFrame.spec.js).
export const SCROLL_SCRIPT_HASH =
  'sha256-fY0+Du/jPLDY+u4qX9O+CqH2oyXTqo4Sk/8jqtRcrY0='

export function buildEmailDocument(
  body,
  { enableImages = false, style = '' } = {}
) {
  if (!body) {
    return ''
  }
  // Remote content (images, fonts...) only loads once the reader asks for
  // the images, which keeps tracking pixels off by default, whatever the
  // links are set to. Inline images come embedded by the server as data:
  // URIs.
  const remoteSrc = enableImages ? ' https: http:' : ''
  const csp = [
    "default-src 'none'",
    `script-src '${SCROLL_SCRIPT_HASH}'`,
    `img-src data:${remoteSrc}`,
    `media-src data:${remoteSrc}`,
    `font-src data:${remoteSrc}`,
    "style-src 'unsafe-inline'",
    "form-action 'none'",
  ].join('; ')
  return (
    '<!DOCTYPE html><html><head><meta charset="utf-8">' +
    `<meta http-equiv="Content-Security-Policy" content="${csp}">` +
    '<base target="_blank">' +
    `<style>${style}</style>` +
    '</head><body>' +
    body +
    `<script>${SCROLL_SCRIPT}</script>` +
    '</body></html>'
  )
}
