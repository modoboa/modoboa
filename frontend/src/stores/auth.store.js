import Cookies from 'js-cookie'

import { defineStore } from 'pinia'
import { computed, inject, ref } from 'vue'
import gettext, { DEFAULT_LANGUAGE } from '@/plugins/gettext'
import { useLocale } from 'vuetify'
import router from '@/router/index.js'
import { createUserManager } from '@/oidc'

import repository from '@/api/repository'
import accountApi from '@/api/account'
import accountsApi from '@/api/accounts'
import authApi from '@/api/auth.js'
import { toGettextLocale } from '@/utils'
import { useGlobalConfig } from '@/config'

export const useAuthStore = defineStore('auth', () => {
  const config = useGlobalConfig()
  const authUser = ref(null)
  const isAuthenticated = ref(false)
  const { current } = useLocale()

  const manager = createUserManager(config)
  const fidoCreds = ref([])

  const userHasMailbox = computed(() => {
    return authUser.value.mailbox !== null
  })

  const accountLanguage = computed(() => {
    return toGettextLocale(authUser.value.language)
  })

  function applyLanguage() {
    // Only switch to locales vue3-gettext actually knows about, falling
    // back to the default language otherwise so we never select an
    // unsupported locale.
    const locale =
      accountLanguage.value in gettext.available
        ? accountLanguage.value
        : DEFAULT_LANGUAGE
    gettext.current = locale
    current.value = locale
  }

  async function fetchUser() {
    const resp = await accountApi.getMe()
    authUser.value = resp.data
    applyLanguage()
    isAuthenticated.value = true
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

  async function editFidoCred(id, data) {
    return authApi.editFido(id, data).then((res) => {
      for (let i = 0; i < fidoCreds.value.length; i++) {
        if (fidoCreds.value[i].id === id) {
          fidoCreds.value[i] = res.data
          break
        }
      }
      return res
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

  async function validateAccess() {
    // Dev-only: skip OIDC entirely and treat the session as authenticated so
    // the UI can be browsed against the MSW mocks. No effect in production
    // (VITE_MOCK_API is unset there).
    if (import.meta.env.VITE_MOCK_API || globalThis.__MODOBOA_MOCK_API__) {
      if (!isAuthenticated.value || !authUser.value) {
        await fetchUser()
      }
      return true
    }
    const user = await manager.getUser()
    if (!user || user.expired) {
      return false
    }
    repository.defaults.headers.common.Authorization = `Bearer ${user.access_token}`
    repository.defaults.headers.post['Content-Type'] = 'application/json'
    if (!isAuthenticated.value || !authUser.value) {
      await fetchUser()
    }
    return true
  }

  async function login() {
    if (import.meta.env.VITE_MOCK_API || globalThis.__MODOBOA_MOCK_API__) {
      await fetchUser()
      router.push({ name: 'Dashboard' })
      return
    }
    try {
      await manager.signinRedirect()
    } catch (error) {
      console.error('Error logging in:', error)
    }
  }

  async function completeLogin(redirectUrl) {
    try {
      const user = await manager.signinCallback()
      repository.defaults.headers.common.Authorization = `Bearer ${user.access_token}`
      repository.defaults.headers.post['Content-Type'] = 'application/json'
      await fetchUser()
      const previousPage = sessionStorage.getItem('previousPage')
      // Redirect the user to the previous page if available
      if (previousPage) {
        window.location.href = previousPage
      } else {
        // Redirect to a default page if the previous page is not available
        router.push(redirectUrl)
      }
      return user
    } catch (error) {
      console.error('Error completing login:', error)
      // Redirect to Dashboard so the router will attempt again login
      router.push({ name: 'Dashboard' })
      return null
    }
  }

  // Set once the logout has started: requests still in flight answer 401
  // and call $reset() again (api/repository.js). A second signoutRedirect()
  // would find the user already removed, go out without id_token_hint and
  // make the provider ask for a confirmation the user already gave.
  let loggingOut = false

  async function logout() {
    if (loggingOut) {
      return
    }
    loggingOut = true
    // Read before anything is cleared: the ID token lets the provider end
    // the session without asking again (OIDC RP-Initiated Logout).
    const user = await manager.getUser().catch(() => null)
    delete repository.defaults.headers.common.Authorization
    authUser.value = {}
    isAuthenticated.value = false
    if (import.meta.env.VITE_MOCK_API || globalThis.__MODOBOA_MOCK_API__) {
      loggingOut = false
      router.push({ name: 'Login' })
      return
    }
    await manager.signoutRedirect(
      user?.id_token ? { id_token_hint: user.id_token } : {}
    )
  }

  async function $reset() {
    await logout()
  }

  async function updateAccount(data) {
    return accountApi.updateMe(data).then((response) => {
      const newAuthUser = { ...authUser.value, ...response.data }
      delete newAuthUser.password
      authUser.value = { ...newAuthUser }
      applyLanguage()
    })
  }

  async function updatePassword(data) {
    return accountApi.setPassword(data)
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
    accountLanguage,
    completeLogin,
    logout,
    isAuthenticated,
    userHasMailbox,
    fidoCreds,
    validateAccess,
    fetchUser,
    getAccessToken,
    getFidoCreds,
    addFidoCred,
    deleteFidoCreds,
    editFidoCred,
    login,
    $reset,
    updateAccount,
    updatePassword,
    finalizeTFASetup,
  }
})
