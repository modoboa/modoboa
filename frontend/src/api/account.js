import repository from './repository'

const resource = 'account'

export default {
  getMe() {
    return repository.get(`/${resource}/me/`)
  },
  checkPassword(value) {
    return repository.post(`/${resource}/me/password/`, { password: value })
  },
  verifyTFACode(code) {
    const payload = { code }
    return repository.post(`${resource}/tfa/verify/`, payload)
  },
  startTFASetup() {
    return repository.post(`${resource}/tfa/setup/`)
  },
  getKeyForTFASetup() {
    return repository.get(`${resource}/tfa/setup/key/`)
  },
  finalizeTFASetup(pinCode) {
    const payload = { pin_code: pinCode }
    return repository.post(`${resource}/tfa/setup/check/`, payload)
  },
  disableTFA(data) {
    return repository.post(`${resource}/tfa/disable/`, data)
  },
  resetRecoveryCodes(data) {
    return repository.post(`${resource}/tfa/reset_codes/`, data)
  },
  getForward() {
    return repository.get(`${resource}/forward/`)
  },
  setForward(data) {
    return repository.post(`${resource}/forward/`, data)
  },
  getAPIToken() {
    return repository.get(`${resource}/api_token/`)
  },
  createAPIToken() {
    return repository.post(`${resource}/api_token/`)
  },
  deleteAPIToken() {
    return repository.delete(`${resource}/api_token/`)
  },
  getARMessage() {
    return repository.get(`${resource}/armessage/`)
  },
  setARMessage(data) {
    return repository.put(`${resource}/armessage/`, data)
  },
  getFilterSets() {
    return repository.get(`${resource}/filtersets/`)
  },
  downloadFilterSet(filterSetName) {
    return repository.get(`${resource}/filtersets/${filterSetName}/download/`)
  },
  createFilterSet(data) {
    return repository.post(`${resource}/filtersets/`, data)
  },
  activateFilterSet(filterSetName) {
    return repository.post(`${resource}/filtersets/${filterSetName}/activate/`)
  },
  deleteFilterSet(filterSetName) {
    return repository.delete(`${resource}/filtersets/${filterSetName}/`)
  },
  saveFilterSet(filterSetName, data) {
    return repository.put(`${resource}/filtersets/${filterSetName}/`, data)
  },
  getFilterConditionTemplates() {
    return repository.get(`${resource}/filtersets/condition_templates/`)
  },
  getFilterActionTemplates() {
    return repository.get(`${resource}/filtersets/action_templates/`)
  },
  getFilters(filterSetName) {
    return repository.get(`${resource}/filtersets/${filterSetName}/filters/`)
  },
  createFilter(filterSetName, data) {
    return repository.post(
      `${resource}/filtersets/${filterSetName}/filters/`,
      data
    )
  },
  updateFilter(filterSetName, filter, data) {
    return repository.put(
      `${resource}/filtersets/${filterSetName}/filters/${filter}/`,
      data
    )
  },
  disableFilter(filterSetName, filter) {
    return repository.post(
      `${resource}/filtersets/${filterSetName}/filters/${filter}/disable/`
    )
  },
  moveFilterDown(filterSetName, filter) {
    return repository.post(
      `${resource}/filtersets/${filterSetName}/filters/${filter}/move_down/`
    )
  },
  moveFilterUp(filterSetName, filter) {
    return repository.post(
      `${resource}/filtersets/${filterSetName}/filters/${filter}/move_up/`
    )
  },
  enableFilter(filterSetName, filter) {
    return repository.post(
      `${resource}/filtersets/${filterSetName}/filters/${filter}/enable/`
    )
  },
  deleteFilter(filterSetName, filter) {
    return repository.delete(
      `${resource}/filtersets/${filterSetName}/filters/${filter}/`
    )
  },
  getAvailableApplications() {
    return repository.get(`${resource}/available_applications/`)
  },
}
