import repository from './repository'

export default {
  getTheme() {
    return repository.get(`/theme/`)
  },
}
