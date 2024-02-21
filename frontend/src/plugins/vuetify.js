/**
 * plugins/vuetify.js
 *
 * Framework documentation: https://vuetifyjs.com`
 */

// Styles
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

// Composables
import { createVuetify } from 'vuetify'

// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
export default createVuetify({
  theme: {
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
  styles: { configFile: 'src/styles/settings.scss' },
  defaults: {
    VCard: {
      class: 'pa-2',
      VCardTitle: { class: 'd-flex', style: 'align-items: center;' },
    },
  },
})
