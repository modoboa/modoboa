import repository from '@/api/repository'

const resource = 'migrations'

export default {
  getMigrations (query) {
    return repository.get(`/${resource}/`, query)
  },
  getMigration (slug, query) {
    return repository.get(`/${resource}/${slug}/`, query)
  },
  deleteMigration (slug) {
    return repository.delete(`/${resource}/${slug}/`)
  }
}
