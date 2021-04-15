import domainApi from '@/api/domains'

const state = {
  domains: []
}

const getters = {
  domains: state => state.domains,
  getDomainByName: state => name => {
    return state.domains.find(domain => domain.name === name)
  }
}

const mutations = {
  SET_DOMAINS (state, domains) {
    state.domains = domains
  }
}

const actions = {
  fetchDomains ({ commit }) {
    domainApi.getDomains().then(resp => {
      commit('SET_DOMAINS', resp.data)
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
