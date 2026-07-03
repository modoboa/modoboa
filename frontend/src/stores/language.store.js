import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import languagesApi from '@/api/languages'
import gettext, { DEFAULT_LANGUAGE } from '@/plugins/gettext'
import { languageHasCoverage } from '@/utils'

export const useLanguageStore = defineStore('language', () => {
  const availableLanguages = ref([])
  const loaded = ref(false)

  const $reset = async () => {
    availableLanguages.value = []
    loaded.value = false
  }

  const getLanguages = async () => {
    const resp = await languagesApi.getAll()
    availableLanguages.value = resp.data
    loaded.value = true
  }

  // Whether a backend language code has actual UI coverage. The source
  // language (English) needs no translations and is always available.
  const hasTranslation = (languageCode) =>
    languageHasCoverage(gettext.translations, languageCode, DEFAULT_LANGUAGE)

  // Languages offered in selectors: only those that are actually
  // translated, so users aren't shown 0%-coverage languages that would
  // just fall back to English. The full list (availableLanguages) is
  // kept for label resolution of existing values.
  const selectableLanguages = computed(() =>
    availableLanguages.value.filter((item) => hasTranslation(item.code))
  )

  const getLanguageLabel = (languageCode) => {
    const language = availableLanguages.value.find(
      (item) => item.code === languageCode
    )
    return language ? language.label : languageCode
  }

  return {
    availableLanguages,
    selectableLanguages,
    getLanguages,
    getLanguageLabel,
    hasTranslation,
    loaded,
    $reset,
  }
})
