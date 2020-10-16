import Vue from 'vue'

// mutation types
const SET_DOMAINS = 'SET_DOMAINS'
const ADD_DOMAIN = 'ADD_DOMAIN'
const UPDATE_DOMAIN = 'UPDATE_DOMAIN'

// initial state
const state = {
  domainsLoaded: false,
  domains: []
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
  }
}

// actions
const actions = {
  getDomains ({ commit }) {
    return Vue.prototype.$axios.get('/domains/').then(response => {
      commit(SET_DOMAINS, { domains: response.data })
    })
  },
  createDomain ({ commit }, data) {
    return Vue.prototype.$axios.post('/domains/', data).then(response => {
      commit(ADD_DOMAIN, { domain: response.data })
    })
  },
  updateDomain ({ commit }, data) {
    return Vue.prototype.$axios.put(`/domains/${data.pk}/`, data).then(response => {
      commit(UPDATE_DOMAIN, { domain: response.data })
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
  }
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
