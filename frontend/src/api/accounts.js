import repository from './repository'

const resource = 'accounts'

export default {
  getAll ({ domain, role }) {
    return repository.get(`/${resource}/`, { params: { domain, role } })
  },
  getRandomPassword () {
    return repository.get(`${resource}/random_password`)
  },
  validate (data) {
    return repository.post(`${resource}/validate/`, data)
  },
  create (data) {
    return repository.post(`${resource}/`, data)
  }
}
