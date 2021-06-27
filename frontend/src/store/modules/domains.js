import Vue from 'vue'
import domainApi from '@/api/domains'

// mutation types
const SET_DOMAINS = 'SET_DOMAINS'
const ADD_DOMAIN = 'ADD_DOMAIN'
const UPDATE_DOMAIN = 'UPDATE_DOMAIN'
const DELETE_DOMAIN = 'DELETE_DOMAIN'
const SET_DOMAIN_ALIASES = 'SET_DOMAIN_ALIASES'
const ADD_DOMAIN_ALIAS = 'ADD_DOMAIN_ALIAS'
const UPDATE_DOMAIN_ALIAS = 'UPDATE_DOMAIN_ALIAS'
const REMOVE_DOMAIN_ALIAS = 'REMOVE_DOMAIN_ALIAS'

// initial state
const state = {
  domainsLoaded: false,
  domains: [],
  domainAliases: []
}

// getters
const getters = {
  domains: state => state.domains,
  getDomainByPk: state => pk => {
    for (var domain of state.domains) {
      if (domain.pk === parseInt(pk, 10)) {
        return domain
      }
    }
    return null
  },
  domainAliases: state => state.domainAliases
}

// actions
const actions = {
  getDomains ({ commit }) {
    return domainApi.getDomains().then(response => {
      commit(SET_DOMAINS, { domains: response.data })
    })
  },
  createDomain ({ commit }, data) {
    return new Promise((resolve, reject) => {
      domainApi.createDomain(data).then(response => {
        commit(ADD_DOMAIN, { domain: response.data })
        resolve(response)
      }).catch(error => {
        reject(error)
      })
    })
  },
  updateDomain ({ commit }, data) {
    return domainApi.updateDomain(data.pk, data).then(response => {
      commit(UPDATE_DOMAIN, { domain: response.data })
    })
  },
  deleteDomain ({ commit }, { id, data }) {
    return domainApi.deleteDomain(id, data).then(resp => {
      commit(DELETE_DOMAIN, id)
    })
  },
  getDomainAliases ({ commit }) {
    return Vue.prototype.$axios.get('/domainaliases/?expand=target').then(response => {
      commit(SET_DOMAIN_ALIASES, response.data)
    })
  },
  addDomainAlias ({ commit }, data) {
    return domainApi.createDomainAlias(data).then(response => {
      commit(ADD_DOMAIN_ALIAS, response.data)
    })
  },
  updateDomainAlias ({ commit }, { id, data }) {
    return domainApi.updateDomainAlias(id, data).then(response => {
      commit(UPDATE_DOMAIN_ALIAS, response.data)
    })
  },
  deleteDomainAlias ({ commit }, domainAliasId) {
    return domainApi.deleteDomainAlias(domainAliasId).then(response => {
      commit(REMOVE_DOMAIN_ALIAS, domainAliasId)
    })
  }
}

// mutations
const mutations = {
  [SET_DOMAINS] (state, { domains }) {
    state.domainsLoaded = true
    state.domains = domains
  },
  [ADD_DOMAIN] (state, { domain }) {
    state.domains.push(domain)
  },
  [UPDATE_DOMAIN] (state, { domain }) {
    state.domains.filter(function (item, pos) {
      if (item.pk === domain.pk) {
        Vue.set(state.domains, pos, domain)
      }
    })
  },
  [DELETE_DOMAIN] (state, domainId) {
    state.domains = state.domains.filter(item => item.pk !== domainId)
  },
  [SET_DOMAIN_ALIASES] (state, domainAliases) {
    state.domainAliases = domainAliases
  },
  [ADD_DOMAIN_ALIAS] (state, domainAlias) {
    state.domainAliases.push(domainAlias)
  },
  [UPDATE_DOMAIN_ALIAS] (state, domainAlias) {
    state.domainAliases.filter((item, pos) => {
      if (item.pk === domainAlias.pk) {
        Vue.set(state.domainAliases, pos, domainAlias)
      }
    })
  },
  [REMOVE_DOMAIN_ALIAS] (state, domainAliasId) {
    state.domainAliases = state.domainAliases.filter(item => item.pk !== domainAliasId)
  }
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
