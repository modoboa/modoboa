import repository from './repository'

export default {
  requestToken(data) {
    return repository.post('/token/', data)
  },
  recoverPassword(data) {
    return repository.post('/password_reset/', data)
  },
  checkSmsTotp(data) {
    return repository.post('/sms_totp/', data)
  },
  changePassword(data) {
    return repository.post('/reset_confirm/', data)
  },
  beginFidoRegistration() {
    return repository.post('/fido/registration/begin/')
  },
  endFidoRegistration(data) {
    return repository.post('/fido/registration/end/', data)
  },
  getAllFidoRegistred() {
    return repository.get('/fido/')
  },
  deleteFido(id) {
    return repository.delete(`/fido/${id}/`)
  },
  editFido(id, data) {
    return repository.put(`/fido/${id}/`, data)
  },
}
