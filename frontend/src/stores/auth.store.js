import Cookies from 'js-cookie'

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import gettext from '@/plugins/gettext'
import router from '@/router/index.js'
import { UserManager } from 'oidc-client-ts'

import repository from '@/api/repository'
import accountApi from '@/api/account'
import accountsApi from '@/api/accounts'

export const useAuthStore = defineStore('auth', () => {
  const authUser = ref({})
  const isAuthenticated = ref(false)
  const manager = new UserManager({
    authority: 'http://localhost:8000/api/o',
    client_id: 'LVQbfIIX3khWR3nDvix1u9yEGHZUxcx53bhJ7FlD',
    redirect_uri: 'http://localhost:3000/login/logged',
    response_type: 'code',
    scope: 'openid read write',
    automaticSilentRenew: true,
    accessTokenExpiringNotificationTime: 60,
    monitorSession: true,
    filterProtocolClaims: true,
    loadUserInfo: true,
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
      return null
    }
    const user = await manager.getUser()
    if (!user) {
      return null
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

  async function login() {
    try {
      await manager.signinRedirect()
    } catch (error) {
      console.error('Error logging in:', error)
    }
  }

  async function completeLogin() {
    try {
      const user = await manager.signinRedirectCallback()
      isAuthenticated.value = true
      const previousPage = sessionStorage.getItem('previousPage')
      // Redirect the user to the previous page if available
      if (previousPage) {
        window.location.href = previousPage
      } else {
        // Redirect to a default page if the previous page is not available
        router.push({ name: 'Dashboard' })
      }
      return user
    } catch (error) {
      console.error('Error completing login:', error)
      return null
    }
  }

  async function $reset() {
    delete repository.defaults.headers.common.Authorization
    authUser.value = {}
    isAuthenticated.value = false
    //TODO: Call the logout callback of OIDC and log out from the IdP
    manager.signoutRedirect()
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
    completeLogin,
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
