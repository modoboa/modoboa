import repository from './repository'

export default {
  getTheme() {
    return repository.get(`/theme/`)
  },
  uploadLogo(logoType, file) {
    const data = new FormData()
    data.append('logo_type', logoType)
    data.append('image', file)
    return repository.post(`/theme/logo/`, data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  clearLogo(logoType) {
    return repository.delete(`/theme/logo/`, {
      params: { logo_type: logoType },
    })
  },
}
