import repository from '@/api/repository'

const resource = 'migrations'

export default {
  getMigrations(params) {
    return repository.get(`/${resource}/`, { params })
  },
  getMigration(slug, query) {
    return repository.get(`/${resource}/${slug}/`, query)
  },
  deleteMigration(slug) {
    return repository.delete(`/${resource}/${slug}/`)
  },
}
