import Vue from 'vue'
import GetTextPlugin from 'vue-gettext'
import translations from '@/translations.json'

Vue.use(GetTextPlugin, {
  autoAddKeyAttributes: true,
  availableLanguages: {
    en: 'English',
    fr: 'Français'
  },
  translations: translations
})

Vue.filter('translate', value => {
  return !value ? '' : Vue.prototype.$gettext(value.toString())
})
