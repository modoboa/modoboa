import Vue from 'vue'
import domainApi from '@/api/domains'

// mutation types
const SET_DOMAINS = 'SET_DOMAINS'
const ADD_DOMAIN = 'ADD_DOMAIN'
const UPDATE_DOMAIN = 'UPDATE_DOMAIN'
const DELETE_DOMAIN = 'DELETE_DOMAIN'

// initial state
const state = {
  domainsLoaded: false,
  domains: []
}

// getters
const getters = {
  domains: state => state.domains,
  getDomainByPk: state => pk => {
    for (const domain of state.domains) {
      if (domain.pk === parseInt(pk, 10)) {
        return domain
      }
    }
    return null
  }
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
    state.domains.forEach(function (item, pos) {
      if (item.pk === domain.pk) {
        Vue.set(state.domains, pos, domain)
      }
    })
  },
  [DELETE_DOMAIN] (state, domainId) {
    state.domains = state.domains.filter(item => item.pk !== domainId)
  }
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
