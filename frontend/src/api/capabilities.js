import repository from './repository'

export default {
  getCapabilities() {
    return repository.get(`/capabilities/`)
  },
}
