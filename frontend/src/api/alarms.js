import repository from './repository'

const resource = 'alarms'

export default {
  getAll (params) {
    return repository.get(`${resource}/`, { params })
  },
  switchStatus (alarmId, data) {
    return repository.patch(`${resource}/${alarmId}/switch/`, data)
  },
  delete (alarmId) {
    return repository.delete(`${resource}/${alarmId}/`)
  }
}
