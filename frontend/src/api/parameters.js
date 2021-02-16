import repository from './repository'

const resource = 'parameters'

export default {
  getApplications () {
    return repository.get(`/${resource}/applications/`)
  },
  getAppliction (app) {
    return repository.get(`/${resource}/${app}/`)
  },
  getApplicationStructure (app) {
    return repository.get(`/${resource}/structure/?app=${app}`)
  },
  saveApplication (app, data) {
    return repository.post(`/${resource}/${app}/`, data)
  }
}
