import repository from './repository'

const resource = 'parameters'

export default {
  getGlobalApplications() {
    return repository.get(`/${resource}/global/applications/`)
  },
  getGlobalApplication(app) {
    return repository.get(`/${resource}/global/${app}/`)
  },
  getGlobalApplicationStructure(app) {
    return repository.get(`/${resource}/global/structure/?app=${app}`)
  },
  saveGlobalApplication(app, data) {
    return repository.put(`/${resource}/global/${app}/`, data)
  },

  getUserApplications() {
    return repository.get(`/${resource}/user/applications/`)
  },
  getUserApplication(app) {
    return repository.get(`/${resource}/user/${app}/`)
  },
  getUserApplicationStructure(app) {
    return repository.get(`/${resource}/user/structure/?app=${app}`)
  },
  saveUserApplication(app, data) {
    return repository.put(`/${resource}/user/${app}/`, data)
  },
}
