import repository from './repository'

const resource = 'transports'

export default {
  getAll() {
    return repository.get(`/${resource}/`)
  },
}
