import repository from './repository'

export default {
  requestToken (data) {
    return repository.post('/token/', data)
  }
}
