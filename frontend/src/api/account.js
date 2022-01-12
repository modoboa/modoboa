import repository from './repository'

const resource = 'account'

export default {
  getMe () {
    return repository.get(`/${resource}/me/`)
  },
  checkPassword (value) {
    return repository.post(`/${resource}/me/password/`, { password: value })
  },
  verifyTFACode (code) {
    const payload = { code }
    return repository.post(`${resource}/tfa/verify/`, payload)
  },
  startTFASetup () {
    return repository.post(`${resource}/tfa/setup/`)
  },
  getQRCodeForTFASetup () {
    return repository.get(`${resource}/tfa/setup/qr_code/`)
  },
  finalizeTFASetup (pinCode) {
    const payload = { pin_code: pinCode }
    return repository.post(`${resource}/tfa/setup/check/`, payload)
  },
  disableTFA () {
    return repository.post(`${resource}/tfa/disable/`)
  },
  resetRecoveryCodes () {
    return repository.post(`${resource}/tfa/reset_codes/`)
  },
  getForward () {
    return repository.get(`${resource}/forward/`)
  },
  setForward (data) {
    return repository.post(`${resource}/forward/`, data)
  }
}
