import repository from './repository'

export default {
  getComponentsInformation() {
    return repository.get('/admin/components/')
  },
  getNotifications() {
    return repository.get('/admin/notifications/')
  },
  getNewsFeed() {
    return repository.get('/admin/news_feed/')
  },
  getStatistics() {
    return repository.get('/admin/statistics/')
  },
}
