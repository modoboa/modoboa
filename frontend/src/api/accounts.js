import repository from './repository'

const resource = 'accounts'

export default {
  getAll(params) {
    return repository.get(`/${resource}/`, {
      params,
      paramsSerializer: {
        indexes: null,
      },
    })
  },
  get(accountId) {
    return repository.get(`${resource}/${accountId}/`)
  },
  getRandomPassword() {
    return repository.get(`${resource}/random_password/`)
  },
  getCredentials(accountId) {
    return repository.get(`credentials/${accountId}/`, { responseType: 'blob' })
  },
  validate(data) {
    return repository.post(`${resource}/validate/`, data)
  },
  create(data) {
    return repository.post(`${resource}/`, data)
  },
  patch(accountId, data) {
    return repository.patch(`${resource}/${accountId}/`, data)
  },
  delete(accountId, data) {
    return repository.post(`${resource}/${accountId}/delete/`, data)
  },
}
