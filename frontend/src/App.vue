<template>
  <Suspense>
    <router-view />
  </Suspense>
</template>

<script setup>
import { useTheme } from 'vuetify'
import themeApi from '@/api/theme'

const theme = useTheme()

themeApi.getTheme().then((response) => {
  if (
    response.data.theme_primary_color !==
    theme.themes.value.light.colors.primary
  ) {
    theme.themes.value.light.colors.primary = response.data.theme_primary_color
  }
  if (
    response.data.theme_primary_color_light !==
    theme.themes.value.light.colors['primary-lighten-1']
  ) {
    theme.themes.value.light.colors['primary-lighten-1'] =
      response.data.theme_primary_color_light
  }
  if (
    response.data.theme_primary_color_dark !==
    theme.themes.value.light.colors['primary-darken-1']
  ) {
    theme.themes.value.light.colors['primary-darken-1'] =
      response.data.theme_primary_color_dark
  }
  if (
    response.data.theme_secondary_color !==
    theme.themes.value.light.colors.secondary
  ) {
    theme.themes.value.light.colors.secondary =
      response.data.theme_secondary_color
  }
  if (
    response.data.theme_label_color !== theme.themes.value.light.colors.label
  ) {
    theme.themes.value.light.colors.label = response.data.theme_label_color
  }
})
</script>
