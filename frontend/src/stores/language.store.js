import { defineStore } from 'pinia'
import { ref } from 'vue'
import languagesApi from '@/api/languages'

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

  const getLanguageLabel = (languageCode) => {
    const language = availableLanguages.value.find(
      (item) => item.code === languageCode
    )
    return language ? language.label : languageCode
  }

  return {
    availableLanguages,
    getLanguages,
    getLanguageLabel,
    loaded,
    $reset,
  }
})
