import repository from './repository'

const resource = 'account'

export default {
  getMe () {
    return repository.get(`/${resource}/me/`)
  },
  verifyTFACode (code) {
    const payload = { code }
    return repository.post(`${resource}/tfa/verify/`, payload)
  }
}
