import repository from './repository'

const resource = 'mailboxes'

export default {
  getAll() {
    return repository.get(`${resource}/`)
  },
}
