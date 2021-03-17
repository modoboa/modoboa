import repository from './repository'

const resource = 'identities'

export default {
  getAll () {
    return repository.get(`${resource}/`)
  }
}
