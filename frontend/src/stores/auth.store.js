import Cookies from 'js-cookie'

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import gettext from '@/plugins/gettext'
import router from '@/router/index.js'
import { UserManager } from 'oidc-client-ts'

import repository from '@/api/repository'
import accountApi from '@/api/account'
import accountsApi from '@/api/accounts'
import authApi from '@/api/auth.js'

import { useGlobalConfig } from '@/main'

export const useAuthStore = defineStore('auth', () => {
  const config = useGlobalConfig()
  const authUser = ref(null)
  const isAuthenticated = ref(false)
  const manager = new UserManager({
    authority: config.OAUTH_AUTHORITY_URL,
    client_id: config.OAUTH_CLIENT_ID,
    redirect_uri: config.OAUTH_REDIRECT_URI,
    response_type: 'code',
    scope: 'openid read write',
    automaticSilentRenew: true,
    accessTokenExpiringNotificationTime: 60,
    monitorSession: true,
    filterProtocolClaims: true,
    loadUserInfo: true,
  })
  const fidoCreds = ref([])

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

  async function getFidoCreds() {
    return authApi.getAllFidoRegistred().then((resp) => {
      fidoCreds.value = resp.data
      if (fidoCreds.value.length > 0) {
        authUser.value.tfa_enabled = true
        authUser.value.webauthn_enabled = true
      }
      return resp
    })
  }

  async function addFidoCred(result) {
    return authApi.endFidoRegistration(result).then((res) => {
      getFidoCreds()
      return res
    })
  }

  async function deleteFidoCreds(id) {
    return authApi.deleteFido(id).then((res) => {
      fidoCreds.value = fidoCreds.value.filter((cred) => cred.id !== id)
      authUser.value.tfa_enabled = res.data.tfa_enabled
      if (!res.data.tfa_enabled) {
        authUser.value.webauthn_enabled = false
      }
    })
  }

  function getAccessToken() {
    return manager.getUser().then((user) => {
      if (!user) {
        return null
      }
      return user.access_token
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
    return fetchUser()
  }

  async function validateAccess() {
    const user = await manager.getUser()
    if (!user || user.expired) {
      manager.signinRedirect()
      return
    }
    repository.defaults.headers.common.Authorization = `Bearer ${user.access_token}`
    repository.defaults.headers.post['Content-Type'] = 'application/json'
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

  function finalizeTFASetup(pinCode) {
    return accountApi.finalizeTFASetup(pinCode).then((response) => {
      const cookie = Cookies.withAttributes({ sameSite: 'strict' })
      cookie.set('token', response.data.access)
      cookie.set('refreshToken', response.data.refresh)
      fetchUser()
      return response
    })
  }

  return {
    authUser,
    completeLogin,
    isAuthenticated,
    userHasMailbox,
    fidoCreds,
    validateAccess,
    fetchUser,
    getAccessToken,
    getFidoCreds,
    addFidoCred,
    deleteFidoCreds,
    initialize,
    login,
    $reset,
    updateAccount,
    finalizeTFASetup,
  }
})
