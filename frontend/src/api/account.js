import repository from './repository'

const resource = 'account'

export default {
  getMe () {
    return repository.get(`/${resource}/me/`)
  }
}
