function getAbsoluteUrl(url) {
  if (!url.startsWith('http')) {
    return `${location.protocol}//${location.host}${url}`
  }
  return url
}

/**
 * Convert an internal gettext locale code to a BCP 47 language tag.
 *
 * vue3-gettext uses locale identifiers such as `pt_BR` (with an
 * underscore), while the `Intl` API (used by luxon and filesize) only
 * accepts BCP 47 tags such as `pt-BR`. Passing an underscore form to
 * `Intl` throws a `RangeError`, which crashes component rendering.
 */
function localeToBCP47(locale) {
  return locale ? locale.replace(/_/g, '-') : locale
}

export { getAbsoluteUrl, localeToBCP47 }
