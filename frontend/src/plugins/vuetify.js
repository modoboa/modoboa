/**
 * plugins/vuetify.js
 *
 * Framework documentation: https://vuetifyjs.com`
 */

// Styles
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
import '@/styles/main.scss'
import {
  cs,
  de,
  el,
  en,
  es,
  fi,
  fr,
  it,
  ja,
  nl,
  pl,
  pt,
  ru,
  sv,
  tr,
  zhHans,
} from 'vuetify/locale'

// Composables
import { createVuetify } from 'vuetify'

// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
export default createVuetify({
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary: '#046BF8',
          'primary-lighten-1': '#3688F9',
          'primary-darken-1': '#0350BA',
          secondary: '#F18429',
          label: '#616161',
        },
      },
    },
  },
  locale: {
    locale: 'en',
    fallback: 'en',
    messages: {
      cs,
      de,
      el,
      en,
      es,
      fi,
      fr,
      it,
      ja,
      nl,
      pl,
      pt,
      ru,
      sv,
      tr,
      zhHans,
    },
  },
  styles: { configFile: 'src/styles/settings.scss' },
  defaults: {
    VBtn: {
      class: 'text-uppercase',
      style: 'letter-spacing: 0.05em',
    },
    VCard: {
      class: 'pa-2',
      VCardTitle: { class: 'd-flex', style: 'align-items: center;' },
    },
  },
})
