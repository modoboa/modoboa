import repository from './repository'

export default {
  getComponentsInformation() {
    return repository.get('/admin/components/')
  },
  getNotifications() {
    return repository.get('/admin/notifications/')
  },
}
