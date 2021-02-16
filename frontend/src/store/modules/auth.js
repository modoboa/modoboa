import Cookies from 'js-cookie'

import repository from '@/api/repository'
import account from '@/api/account'

function setupAxios (token) {
  repository.defaults.headers.common.Authorization = `Bearer ${token}`
  repository.defaults.headers.post['Content-Type'] = 'application/json'
}

function fetchUser (commit) {
  return account.getMe().then(resp => {
    commit('SET_AUTH_USER', { authUser: resp.data, isAuthenticated: true })
  })
}

const state = () => ({
  authUser: {},
  isAuthenticated: false
})

const getters = {
  isAuthenticated: state => state.isAuthenticated,
  authUser: state => state.authUser
}

const mutations = {
  SET_AUTH_USER (state, { authUser, isAuthenticated }) {
    state.authUser = authUser
    state.isAuthenticated = isAuthenticated
  },
  LOGOUT_USER (state) {
    state.authUser = null
    state.isAuthenticated = false
  }
}

const actions = {
  initialize ({ commit, state }) {
    if (state.isAuthenticated) {
      return
    }
    const token = Cookies.get('token')
    if (!token) {
      return
    }
    setupAxios(token)
    return fetchUser(commit)
  },
  logout ({ commit }) {
    return new Promise((resolve, reject) => {
      delete repository.defaults.headers.common.Authorization
      Cookies.remove('token')
      Cookies.remove('refreshToken')
      commit('LOGOUT_USER')
      resolve()
    })
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
