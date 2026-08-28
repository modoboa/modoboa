import repository from './repository'

export default {
  requestToken(data) {
    return repository.post('/token/', data)
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
