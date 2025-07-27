function getAbsoluteUrl(url) {
  if (!url.startsWith('http')) {
    return `${location.protocol}//${location.host}${url}`
  }
  return url
}

export { getAbsoluteUrl }
