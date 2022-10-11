import repository from './repository'

export default {
  requestToken (data) {
    return repository.post('/token/', data)
  },
  recoverPassword (data) {
    return repository.post('/password_reset/', data)
  },
  changePassword (data, id, token) {
    return repository.post('/reset_confirm/' + id + '/' + token, data)
  }
}
