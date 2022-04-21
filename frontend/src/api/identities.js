import repository from './repository'

const resource = 'identities'

export default {
  getAll () {
    return repository.get(`${resource}/`)
  },
  exportAll () {
    return repository.get(`/${resource}/export/`)
  },
  importFromCSV (data) {
    return repository.post(`/${resource}/import/`, data, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}
