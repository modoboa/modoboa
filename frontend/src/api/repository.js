import axios from 'axios'
import Cookies from 'js-cookie'
import router from '@/router'
import gettext from '@/plugins/gettext'
import { useAuthStore, useBusStore } from '@/stores'
import { getErrorMessage } from '@/api/errors'

const { $gettext } = gettext

const _axios = axios.create()

_axios.interceptors.request.use(
  async function (config) {
    const authStore = useAuthStore()
    if (authStore.isAuthenticated) {
      const token = await authStore.getAccessToken()
      if (authStore.authUser) {
        config.headers['Accept-Language'] = authStore.authUser.language
      }
      config.headers['Authorization'] = `Bearer ${token}`
    }
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
    if (!error.response) {
      // No answer at all: server unreachable, network down, timeout...
      // The promise must still be rejected, or callers would go on with
      // an undefined response.
      if (!axios.isCancel(error) && !error.config?.ignoreErrors) {
        useBusStore().displayNotification({
          msg: $gettext(
            'Unable to reach the server, please check your connection'
          ),
          type: 'error',
        })
      }
      return Promise.reject(error)
    }
    if (error.response.status === 418) {
      router.push({ name: 'TwoFA' })
      return Promise.reject(error)
    }
    if (error.response.status === 429) {
      return Promise.reject(error)
    }
    if (error.response.status !== 401 || router.currentRoute.name === 'Login') {
      if (
        error.response.status !== 518 &&
        error.config &&
        !error.config.ignoreErrors
      ) {
        const busStore = useBusStore()
        const msg =
          getErrorMessage(error.response.data) ||
          $gettext('An unexpected error occurred (code %{ status })', {
            status: error.response.status,
          })
        busStore.displayNotification({
          msg,
          type: 'error',
        })
      }
      return Promise.reject(error)
    }
    const refreshToken = Cookies.get('refreshToken')
    const authStore = useAuthStore()
    if (error.config.url.endsWith('/token/refresh/') || !refreshToken) {
      authStore.$reset()
      if (router.currentRoute.name !== 'Login') {
        router.push({ name: 'Login' })
      }
      return Promise.reject(error)
    }
    return _axios
      .post('/token/refresh/', { refresh: refreshToken })
      .then((resp) => {
        Cookies.set('token', resp.data.access, { sameSite: 'strict' })
        _axios.defaults.headers.common.Authorization = `Bearer ${resp.data.access}`
        const config = error.config
        config.headers.Authorization = `Bearer ${resp.data.access}`
        return new Promise((resolve, reject) => {
          _axios
            .request(config)
            .then((resp) => {
              resolve(resp)
            })
            .catch((error) => {
              reject(error)
            })
        })
      })
      .catch((error) => {
        // Without "return", a failed refresh would resolve with undefined
        return Promise.reject(error)
      })
  }
)

export default _axios
