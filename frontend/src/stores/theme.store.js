import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useTheme } from 'vuetify'

export const useThemeStore = defineStore('theme', () => {
  const theme = useTheme()
  const currentTheme = ref(theme.global.name.value)

  function toggleTheme() {
    const nextTheme =
      theme.global.name.value === 'modoboaDark' ? 'light' : 'modoboaDark'
    theme.global.name.value = nextTheme
    currentTheme.value = nextTheme
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('modoboa_theme', nextTheme)
    }
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('data-theme', nextTheme)
    }
  }

  return {
    currentTheme,
    toggleTheme,
  }
})
