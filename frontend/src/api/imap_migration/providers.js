import repository from '@/api/repository'

const resource = 'email-providers'

export default {
  getProviders(params) {
    return repository.get(`/${resource}/`, { params })
  },
  getProvider(providerId) {
    return repository.get(`/${resource}/${providerId}/`)
  },
  createProvider(params) {
    return repository.post(`/${resource}/`, params)
  },
  updateProvider(slug, params) {
    return repository.put(`/${resource}/${slug}/`, params)
  },
  patchProvider(providerId, params) {
    return repository.patch(`/${resource}/${providerId}/`, params)
  },
  deleteProvider(slug) {
    return repository.delete(`/${resource}/${slug}/`)
  },
  checkProvider(params) {
    return repository.post(`/${resource}/check_connection/`, params)
  },
  checkAssociatedDomain(params) {
    return repository.post(`/${resource}/check_associated_domain/`, params)
  },
}
