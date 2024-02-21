import Cookies from 'js-cookie'

import { defineStore } from 'pinia'
import { ref } from 'vue'
import gettext from '@/plugins/gettext'

import repository from '@/api/repository'
import accountApi from '@/api/account'
import accountsApi from '@/api/accounts'
import authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
    const authUser = ref({})
    const isAuthenticated = ref(false)

    async function fetchUser() {
        return accountApi.getMe().then((resp) => {
            gettext.current = resp.data.language
            authUser.value = resp.data
            isAuthenticated.value = true
        })
    }

    async function initialize() {
        const token = Cookies.get('token')
        if (!token) {
            return
        }
        repository.defaults.headers.common.Authorization = `Bearer ${token}`
        repository.defaults.headers.post['Content-Type'] = 'application/json'
        return fetchUser()
    }

    async function login(payload) {
        const resp = await authApi.requestToken(payload)
        const cookiesAttributes = { sameSite: 'strict' }
        if (payload.rememberMe) {
            cookiesAttributes.expires = 90
        }

        const cookie = Cookies.withAttributes(cookiesAttributes)
        cookie.set('token', resp.data.access)
        cookie.set('refreshToken', resp.data.refresh)
        initialize()
    }
    async function $reset() {
        delete repository.defaults.headers.common.Authorization
        Cookies.remove('token')
        Cookies.remove('refreshToken')
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
        fetchUser,
        initialize,
        login,
        $reset,
        updateAccount,
        finalizeTFASetup,
    }
})
