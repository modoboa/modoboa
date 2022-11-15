import repository from './repository'

const resource = 'alarms'

export default {
  getAll (params) {
    return repository.get(`${resource}/`, { params })
  }
}
