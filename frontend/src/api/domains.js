import repository from './repository'

const domainResource = 'domains'
const domainAliasResource = 'domainaliases'

export default {
  getDomains() {
    return repository.get(`/${domainResource}/`)
  },
  getDomain(domainId) {
    return repository.get(`/${domainResource}/${domainId}/`)
  },
  getDomainDNSDetail(domainId) {
    return repository.get(`/${domainResource}/${domainId}/dns_detail/`)
  },
  getDomainDmarcAlignment(domainId, period) {
    return repository.get(
      `${domainResource}/${domainId}/dmarc/alignment_stats/`,
      { params: { period } }
    )
  },
  getDomainAliases(domain) {
    let url = `/${domainAliasResource}/`
    if (domain !== undefined) {
      url += `?domain=${domain}`
    }
    return repository.get(url)
  },
  getDomainAdministrators(domainId) {
    return repository.get(`/${domainResource}/${domainId}/administrators/`)
  },
  addDomainAdministrator(domainId, accountId) {
    return repository.post(
      `/${domainResource}/${domainId}/administrators/add/`,
      { account: accountId }
    )
  },
  removeDomainAdministrator(domainId, accountId) {
    return repository.post(
      `/${domainResource}/${domainId}/administrators/remove/`,
      { account: accountId }
    )
  },
  createDomain(data) {
    return repository.post(`/${domainResource}/`, data)
  },
  updateDomain(domainId, data) {
    return repository.put(`/${domainResource}/${domainId}/`, data)
  },
  patchDomain(domainId, data) {
    return repository.patch(`/${domainResource}/${domainId}/`, data)
  },
  deleteDomain(domainId, data) {
    return repository.post(`/${domainResource}/${domainId}/delete/`, data)
  },
  createDomainAlias(data) {
    return repository.post(`/${domainAliasResource}/`, data)
  },
  updateDomainAlias(aliasId, data) {
    return repository.put(`/${domainAliasResource}/${aliasId}/`, data)
  },
  deleteDomainAlias(aliasId) {
    return repository.delete(`/${domainAliasResource}/${aliasId}/`)
  },
  exportAll() {
    return repository.get(`/${domainResource}/export/`)
  },
  importFromCSV(data) {
    return repository.post(`/${domainResource}/import/`, data, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
}
