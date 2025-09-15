import { ref } from 'vue'
import { useTheme } from 'vuetify'
import themeApi from '@/api/theme'

export function useModoboaTheme() {
  const vTheme = useTheme()
  const theme = ref(null)

  const enableTheme = async () => {
    const response = await themeApi.getTheme()

    theme.value = response.data
    if (
      theme.value.theme_primary_color !==
      vTheme.themes.value.light.colors.primary
    ) {
      vTheme.themes.value.light.colors.primary = theme.value.theme_primary_color
    }
    if (
      theme.value.theme_primary_color_light !==
      vTheme.themes.value.light.colors['primary-lighten-1']
    ) {
      vTheme.themes.value.light.colors['primary-lighten-1'] =
        theme.value.theme_primary_color_light
    }
    if (
      theme.value.theme_primary_color_dark !==
      vTheme.themes.value.light.colors['primary-darken-1']
    ) {
      vTheme.themes.value.light.colors['primary-darken-1'] =
        theme.value.theme_primary_color_dark
    }
    if (
      theme.value.theme_secondary_color !==
      vTheme.themes.value.light.colors.secondary
    ) {
      vTheme.themes.value.light.colors.secondary =
        theme.value.theme_secondary_color
    }
    if (
      theme.value.theme_label_color !== vTheme.themes.value.light.colors.label
    ) {
      vTheme.themes.value.light.colors.label = theme.value.theme_label_color
    }
  }

  return { theme, enableTheme }
}
