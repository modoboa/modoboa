import repository from './repository'

const resource = 'logs'

export default {
  getAuditTrail(params) {
    return repository.get(`/${resource}/audit-trail/`, { params })
  },
  getAuditActions() {
    return repository.get(`/${resource}/audit-trail/actions/`)
  },
  getMessages(params) {
    return repository.get(`/${resource}/messages/`, { params })
  },
}
