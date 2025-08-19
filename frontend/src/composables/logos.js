import { computed } from 'vue'
import { useGlobalConfig } from '@/main'

export function useLogos() {
  const globalConfig = useGlobalConfig()

  const menuLogoPath = computed(() => {
    if (globalConfig.MENU_LOGO_PATH) {
      return globalConfig.MENU_LOGO_PATH
    }
    const imgUrl = new URL(
      '@/assets/Modoboa_RVB-BLANC-SANS.png',
      import.meta.url
    ).href
    return imgUrl
  })

  const creationFormLogoPath = computed(() => {
    if (globalConfig.CREATION_FORM_LOGO_PATH) {
      return globalConfig.CREATION_FORM_LOGO_PATH
    }
    const imgUrl = new URL(
      '@/assets/Modoboa_RVB-BLEU-SANS.png',
      import.meta.url
    ).href
    return imgUrl
  })

  return {
    menuLogoPath,
    creationFormLogoPath,
  }
}
