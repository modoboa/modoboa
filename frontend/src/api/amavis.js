import repository from './repository'

export default {
  getQuarantineContent(params) {
    return repository.get('/amavis/quarantine/', { params })
  },
  releaseSelection(data) {
    return repository.post('/amavis/quarantine/release_selection/', data)
  },
  releaseMessage(mailid, data) {
    return repository.post(`/amavis/quarantine/${mailid}/release/`, data)
  },
  deleteSelection(data) {
    return repository.post('/amavis/quarantine/delete_selection/', data)
  },
  deleteMessage(mailid, data) {
    return repository.post(`/amavis/quarantine/${mailid}/delete/`, data)
  },
  markMessageSelection(data) {
    return repository.post('/amavis/quarantine/mark_selection/', data)
  },
  getMessageContent(mailid, rcpt, secretId) {
    const params = { rcpt }
    if (secretId) {
      params.secret_id = secretId
    }
    return repository.get(`/amavis/quarantine/${mailid}/`, { params })
  },
  getMessageHeaders(mailid, rcpt, secretId) {
    const params = { rcpt }
    if (secretId) {
      params.secret_id = secretId
    }
    return repository.get(`/amavis/quarantine/${mailid}/headers/`, { params })
  },
  getDomainPolicy(domainId) {
    return repository.get(`/amavis/policies/${domainId}/`)
  },
  updateDomainPolicy(domainId, data) {
    return repository.patch(`/amavis/policies/${domainId}/`, data)
  },
}
