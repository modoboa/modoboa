import repository from './repository'

export default {
  getManifests() {
    return repository.get('/frontend/plugins/')
  },
}
