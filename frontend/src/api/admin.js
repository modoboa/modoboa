import repository from './repository'

export default {
  getComponentsInformation () {
    return repository.get('/admin/components')
  }
}
