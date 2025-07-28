import repository from './repository'

export default {
  getQuarantineContent(params) {
    return repository.get('/amavis/quarantine/', { params })
  },
}
