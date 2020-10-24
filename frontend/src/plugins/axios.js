'use strict'

import Vue from 'vue'
import axios from 'axios'
import Cookies from 'js-cookie'

import router from '../router'
import store from '../store'

// Full config:  https://github.com/axios/axios#request-config
axios.defaults.baseURL = process.VUE_APP_API_BASE_URL || ''
// axios.defaults.headers.common['Authorization'] = AUTH_TOKEN;
// axios.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded';

const config = {
  baseURL: process.env.VUE_APP_API_BASE_URL || ''
  // timeout: 60 * 1000 // Timeout
  // withCredentials: true // Check cross-site Access-Control
}

const _axios = axios.create(config)

_axios.interceptors.request.use(
  function (config) {
    // Do something before request is sent
    return config
  },
  function (error) {
    // Do something with request error
    return Promise.reject(error)
  }
)

// Add a response interceptor
_axios.interceptors.response.use(
  function (response) {
    // Do something with response data
    return response
  },
  function (error) {
    if (error.response.status !== 401) {
      return Promise.reject(error)
    }
    const refreshToken = Cookies.get('refreshToken')
    if (error.config.url.endsWith('/token/refresh/') || !refreshToken) {
      store.dispatch('auth/logout')
      router.push('/login/')
      return Promise.reject(error)
    }
    return _axios.post('/token/refresh/', { refresh: refreshToken }).then(resp => {
      console.log('OK')
      Cookies.set('token', resp.data.access, { sameSite: 'strict' })
      _axios.defaults.headers.common.Authorization = `Bearer ${resp.data.access}`
      const config = error.config
      config.headers.Authorization = `Bearer ${resp.data.access}`
      return new Promise((resolve, reject) => {
        _axios.request(config).then(resp => {
          resolve(resp)
        }).catch(error => {
          reject(error)
        })
      })
    }).catch(error => {
      Promise.reject(error)
    })
  }
)

Plugin.install = function (Vue, options) {
  Vue.axios = _axios
  window.axios = _axios
  Object.defineProperties(Vue.prototype, {
    axios: {
      get () {
        return _axios
      }
    },
    $axios: {
      get () {
        return _axios
      }
    }
  })
}

Vue.use(Plugin)

export default Plugin
