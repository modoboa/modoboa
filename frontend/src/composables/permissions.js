import { computed } from 'vue'
import { useAuthStore } from '@/stores'
import constants from '@/constants.json'

export function usePermissions() {
  const authStore = useAuthStore()

  const canSetRole = computed(() => {
    return [constants.RESELLER, constants.SUPER_ADMIN].includes(
      authStore.authUser.role
    )
  })

  const canAddDomain = computed(() => {
    return [constants.RESELLER, constants.SUPER_ADMIN].includes(
      authStore.authUser.role
    )
  })

  const canViewDomain = computed(() => {
    return [
      constants.DOMAIN_ADMIN,
      constants.RESELLER,
      constants.SUPER_ADMIN,
    ].includes(authStore.authUser.role)
  })

  return {
    canSetRole,
    canAddDomain,
    canViewDomain,
  }
}
