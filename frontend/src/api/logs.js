import repository from './repository'

const resource = 'logs'

export default {
  getAll () {
    return repository.get(`/${resource}/`)
  }
}
