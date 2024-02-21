import repository from './repository'

const resource = 'statistics'

export default {
  getStatistics({ graphSet, period, graphicName, searchQuery, start, end }) {
    const args = {
      gset: graphSet,
      period,
      graphic: graphicName,
      searchquery: searchQuery,
      start: start,
      end: end,
    }
    return repository.get(`${resource}/`, { params: args })
  },
}
