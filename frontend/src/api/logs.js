import repository from './repository'

const resource = 'logs'

export default {
  getAll (params) {
    return repository.get(`/${resource}/`, { params })
  }
}
