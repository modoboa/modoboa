import repository from './repository'

const resource = 'identities'

export default {
  getAll() {
    return repository.get(`${resource}/`)
  },
  exportAll(type) {
    return repository.get(`/${resource}/export/`, { params: { type } })
  },
  importFromCSV(data) {
    return repository.post(`/${resource}/import/`, data, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
}
