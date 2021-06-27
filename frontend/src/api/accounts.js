import repository from './repository'

const resource = 'accounts'

export default {
  getAll ({ domain, role }) {
    return repository.get(`/${resource}/`, { params: { domain, role } })
  },
  get (accountId) {
    return repository.get(`${resource}/${accountId}/`)
  },
  getRandomPassword () {
    return repository.get(`${resource}/random_password`)
  },
  validate (data) {
    return repository.post(`${resource}/validate/`, data)
  },
  create (data) {
    return repository.post(`${resource}/`, data)
  },
  patch (accountId, data) {
    return repository.patch(`${resource}/${accountId}/`, data)
  },
  delete (accountId, data) {
    return repository.post(`${resource}/${accountId}/delete/`, data)
  }
}
