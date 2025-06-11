import { computed } from 'vue'
import { useAuthStore } from '@/stores'

export function usePermissions() {
  const authStore = useAuthStore()

  const canSetRole = computed(() => {
    return ['Resellers', 'SuperAdmins'].includes(authStore.authUser.role)
  })

  const canAddDomain = computed(() => {
    return ['Resellers', 'SuperAdmins'].includes(authStore.authUser.role)
  })

  return {
    canSetRole,
    canAddDomain,
  }
}
