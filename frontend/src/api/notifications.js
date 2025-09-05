import repository from './repository'

export default {
  getNotifications() {
    return repository.get('/notifications/')
  },
}
