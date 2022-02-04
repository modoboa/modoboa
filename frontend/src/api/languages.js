import repository from './repository'

const resource = 'languages'

export default {
  getAll () {
    return repository.get(`/${resource}/`)
  }
}
