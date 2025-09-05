import { computed, ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useAuthStore } from '@/stores'
import { usePermissions } from './permissions'
import parametersApi from '@/api/parameters'
import constants from '@/constants.json'

export async function useAmavis() {
  const authStore = useAuthStore()
  const { $gettext } = useGettext()
  const { canViewDomain } = usePermissions()
  const globalParams = ref(null)

  const manualLearningEnabled = computed(() => {
    if (globalParams.value && globalParams.value.params.manual_learning) {
      if (authStore.authUser.role !== constants.SUPER_ADMIN) {
        if (canViewDomain.value) {
          return (
            globalParams.value.params.domain_level_learning ||
            globalParams.value.params.user_level_learning
          )
        }
        return globalParams.value.params.user_level_learning
      }
      return true
    }
    return false
  })

  const learningRecipients = computed(() => {
    const result = []
    if (authStore.authUser.role === constants.SUPER_ADMIN) {
      result.push({ value: 'global', title: $gettext('Global database') })
    }
    if (globalParams.value.params.domain_level_learning) {
      result.push({ value: 'domain', title: $gettext("Domain's database") })
    }
    if (globalParams.value.params.user_level_learning) {
      result.push({ value: 'user', title: $gettext("User's database") })
    }
    return result
  })

  const resp = await parametersApi.getGlobalApplication('amavis')
  globalParams.value = resp.data

  return {
    learningRecipients,
    manualLearningEnabled,
  }
}
