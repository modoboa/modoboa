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

/**
 * Backend language codes that do not follow the generic
 * `xx-yy` -> `xx_YY` rule when mapped to the frontend locale.
 */
const LANGUAGE_CODE_ALIASES = {
  'zh-hant': 'zh',
}

/**
 * Map a backend language code to the locale identifier used by
 * vue3-gettext.
 *
 * The backend (`modoboa/core/constants.py`) serves codes such as
 * `pt-br` or `zh-hant`, while vue3-gettext expects keys such as `pt_BR`
 * or `zh`. The generic rule turns `xx-yy` into `xx_YY`; aliases handle
 * the cases that rule gets wrong (e.g. `zh-hant`, which must map to the
 * existing `zh` locale instead of a non-existent `zh_HANT`).
 */
function toGettextLocale(code) {
  if (!code) {
    return code
  }
  const alias = LANGUAGE_CODE_ALIASES[code.toLowerCase()]
  if (alias) {
    return alias
  }
  if (code.includes('-')) {
    const [language, region] = code.split('-')
    return `${language}_${region.toUpperCase()}`
  }
  return code
}

export { getAbsoluteUrl, localeToBCP47, toGettextLocale }
