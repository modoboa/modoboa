import Vue from 'vue'
import providerApi from '@/api/imap_migration/providers'

// mutation types
export const ADD_PROVIDER = 'ADD_PROVIDER'
export const UPDATE_PROVIDER = 'SET_PROVIDER'
export const SET_PROVIDERS = 'SET_PROVIDERS'
export const DELETE_PROVIDER = 'DELETE_PROVIDER'

const state = {
  providersLoaded: false,
  providers: []
}

const getters = {
  providers: state => state.providers
}

const actions = {
  getProviders ({ commit }, params) {
    return providerApi.getProviders(params).then(response => {
      commit(SET_PROVIDERS, { providers: response.data })
    })
  },
  createProvider ({ commit }, data) {
    return new Promise((resolve, reject) => {
      providerApi.createProvider(data).then(response => {
        commit(ADD_PROVIDER, { provider: response.data })
        resolve(response)
      }).catch(error => {
        reject(error)
      })
    })
  },
  updateProvider ({ commit }, data) {
    return providerApi.updateProvider(data.id, data).then(response => {
      commit(UPDATE_PROVIDER, { provider: response.data })
    })
  },
  deleteProvider ({ commit }, data) {
    return providerApi.deleteProvider(data.id).then(response => {
      commit(DELETE_PROVIDER, data)
    })
  }
}

const mutations = {
  [SET_PROVIDERS] (state, { providers }) {
    state.providersLoaded = true
    state.providers = providers
  },
  [ADD_PROVIDER] (state, { provider }) {
    state.providers.push(provider)
  },
  [UPDATE_PROVIDER] (state, { provider }) {
    state.providers.forEach(function (item, pos) {
      if (item.pk === provider.pk) {
        Vue.set(state.providers, pos, provider)
      }
    })
  },
  [DELETE_PROVIDER] (state, data) {
    state.providers = state.providers.filter(item => item.id !== data.id)
  }
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
