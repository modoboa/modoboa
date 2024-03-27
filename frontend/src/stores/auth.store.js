import Cookies from 'js-cookie'

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import gettext from '@/plugins/gettext'
import { UserManager } from 'oidc-client-ts'

import repository from '@/api/repository'
import accountApi from '@/api/account'
import accountsApi from '@/api/accounts'
// import authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const authUser = ref({})
  const isAuthenticated = ref(false)
  const manager = new UserManager({
    authority: '/api/o',
    client_id: 'LVQbfIIX3khWR3nDvix1u9yEGHZUxcx53bhJ7FlD',
    // Is client_secret necessary?
    client_secret:
      'fXzG7tq23eXrM7RK41pXHRseuRWnxe4gV0p4A4YXJlF9jva7QfsDft1g7ESYU9AXR35QE0lo2Ti696OXsqb9JHLjtrPxaYmgMSRmRwLCce5hVr3FB2QhfSOThFYhcuuR',
    metadata: {
      authorization_endpoint: '/api/o/authorize/',
      token_endpoint: '/api/o/token/',
    },
    scope: 'read write',
  })

  const userHasMailbox = computed(() => {
    return authUser.value.mailbox !== null
  })

  async function fetchUser() {
    return accountApi.getMe().then((resp) => {
      gettext.current = resp.data.language
      authUser.value = resp.data
      isAuthenticated.value = true
    })
  }

  async function initialize() {
    if (isAuthenticated.value) {
      return
    }
    const user = await manager.getUser()
    if (!user) {
      return
    }
    repository.defaults.headers.common.Authorization = `Bearer ${user.access_token}`
    repository.defaults.headers.post['Content-Type'] = 'application/json'
    return fetchUser()
  }

  async function validateAccess() {
    const user = await manager.getUser()
    if (!user || user.expired) {
      manager.signinRedirect()
    }
  }

  async function login(payload) {
    await manager.signinResourceOwnerCredentials(payload)
    return initialize()
    // const cookiesAttributes = { sameSite: 'strict' }
    // if (payload.rememberMe) {
    //   cookiesAttributes.expires = 90
    // }
  }
  async function $reset() {
    delete repository.defaults.headers.common.Authorization
    authUser.value = {}
    isAuthenticated.value = false
  }

  async function updateAccount(data) {
    return accountsApi.patch(authUser.value.pk, data).then((response) => {
      if (
        response.data.language != authUser.value.language &&
        response.data.language in gettext.available
      ) {
        gettext.current = response.data.language
      }
      const newAuthUser = { ...authUser.value, ...response.data }
      delete newAuthUser.password
      authUser.value = { ...newAuthUser }
    })
  }

  async function finalizeTFASetup(pinCode) {
    return accountApi
      .finalizeTFASetup(pinCode)
      .then((response) => {
        const cookie = Cookies.withAttributes({ sameSite: 'strict' })
        cookie.set('token', response.data.access)
        cookie.set('refreshToken', response.data.refresh)
        initialize()
        return response
      })
      .catch((error) => error)
  }

  return {
    authUser,
    isAuthenticated,
    userHasMailbox,
    validateAccess,
    fetchUser,
    initialize,
    login,
    $reset,
    updateAccount,
    finalizeTFASetup,
  }
})
