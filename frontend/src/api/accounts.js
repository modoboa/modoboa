import repository from './repository'

const resource = 'accounts'

export default {
  getAll ({ domain, role }) {
    return repository.get(`/${resource}/`, { params: { domain, role } })
  }
}
