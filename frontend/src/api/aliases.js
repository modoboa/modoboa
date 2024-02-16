import repository from './repository'

const resource = 'aliases'

export default {
  getAll() {
    return repository.get(`${resource}/`)
  },
  get(aliasId) {
    return repository.get(`${resource}/${aliasId}/`)
  },
  getRandomAddress() {
    return repository.get(`${resource}/random_address/`)
  },
  validate(data) {
    return repository.post(`${resource}/validate/`, data)
  },
  create(data) {
    return repository.post(`${resource}/`, data)
  },
  patch(aliasId, data) {
    return repository.patch(`${resource}/${aliasId}/`, data)
  },
  delete(aliasId) {
    return repository.delete(`${resource}/${aliasId}/`)
  },
}
