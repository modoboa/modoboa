import { createGettext } from 'vue3-gettext'
import translations from '@/locale/translations.json'

const availableLanguages = {
  br: 'Breton',
  cs: 'Czech',
  de: 'German',
  el: 'Greek',
  en: 'English',
  es: 'Spain',
  fi: 'Finnish',
  fr: 'French',
  it: 'Italian',
  ja: 'Japanese',
  nl: 'Dutch',
  pl: 'Polish',
  pt_BR: 'Portuguese (BR)',
  ru: 'Russian',
  sv: 'Swedish',
  tr: 'tr',
  zh: 'Chinese',
}

export default createGettext({
  availableLanguages,
  defaultLanguage: 'en',
  translations: translations,
  silent: true, // stop warnings
})
