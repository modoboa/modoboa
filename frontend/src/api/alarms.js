import repository from './repository'

const resource = 'alarms'

export default {
  getAll () {
    return repository.get(`${resource}/`)
  }
}
