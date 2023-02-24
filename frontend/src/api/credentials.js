import repository from './repository'

export default {
  getCredentials (id) {
    return repository.get(`credentials/${id}/`)
  }
}
