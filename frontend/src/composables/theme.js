import { ref } from 'vue'
import { useTheme } from 'vuetify'
import themeApi from '@/api/theme'

export function useModoboaTheme() {
  const vTheme = useTheme()
  const theme = ref(null)

  const enableTheme = async () => {
    const response = await themeApi.getTheme()

    theme.value = response.data
    const themeName = vTheme.global.name.value
    const themeColors = vTheme.themes.value[themeName].colors
    if (theme.value.theme_primary_color !== themeColors.primary) {
      themeColors.primary = theme.value.theme_primary_color
    }
    if (
      theme.value.theme_primary_color_light !== themeColors['primary-lighten-1']
    ) {
      themeColors['primary-lighten-1'] = theme.value.theme_primary_color_light
    }
    if (
      theme.value.theme_primary_color_dark !== themeColors['primary-darken-1']
    ) {
      themeColors['primary-darken-1'] = theme.value.theme_primary_color_dark
    }
    if (theme.value.theme_secondary_color !== themeColors.secondary) {
      themeColors.secondary = theme.value.theme_secondary_color
    }
    if (theme.value.theme_label_color !== themeColors.label) {
      themeColors.label = theme.value.theme_label_color
    }
  }

  return { theme, enableTheme }
}
