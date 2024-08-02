import { createGettext } from 'vue3-gettext'
import translations from '@/locale/translations.json'

export default createGettext({
  availableLanguages: {
    en: 'English',
    cs: 'Czech',
    de: 'German',
    br: 'Breton',
    el: 'Greek',
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
  },
  defaultLanguage: 'en',
  translations: translations,
  silent: true, // stop warnings
})
