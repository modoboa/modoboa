import repository from './repository'

export default {
  getQuarantineContent(params) {
    return repository.get('/amavis/quarantine/', { params })
  },
  releaseSelection(data) {
    return repository.post('/amavis/quarantine/release_selection/', data)
  },
  deleteSelection(data) {
    return repository.post('/amavis/quarantine/delete_selection/', data)
  },
  markMessageSelection(data) {
    return repository.post('/amavis/quarantine/mark_selection/', data)
  },
  getMessageContent(mailid, rcpt) {
    return repository.get(`/amavis/quarantine/${mailid}/?rcpt=${rcpt}`)
  },
  getMessageHeaders(mailid) {
    return repository.get(`/amavis/quarantine/${mailid}/headers/`)
  },
}
