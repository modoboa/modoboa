import { useAuthStore } from '@/stores'

export default {
  install: (app) => {
    const authStore = useAuthStore()

    app.directive('can', (el, binding) => {
      const permission = binding.value
      if (authStore.authUser) {
        if (
          authUser.authUser.role !== 'SuperAdmins' &&
          authStore.authUser.permissions.indexOf(permission) === -1
        ) {
          el.style.display = 'none'
        }
      }
    })

    app.config.globalProperties.$can = function (permission) {
      if (!authStore.authUser) {
        return false
      }
      if (
        authStore.authUser.role === 'SuperAdmins' ||
        authStore.authUser.permissions.indexOf(permission) !== -1
      ) {
        return true
      }
      return false
    }
  },
}
