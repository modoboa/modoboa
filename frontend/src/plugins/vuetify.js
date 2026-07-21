/**
 * plugins/vuetify.js
 *
 * Framework documentation: https://vuetifyjs.com`
 */

// Styles
// Self-hosted Roboto (no external Google Fonts request). Only the weights
// the app uses (300/400/500/700), latin + latin-ext subsets — enough for
// en/pt_BR and other Western-European text.
import '@fontsource/roboto/latin-300.css'
import '@fontsource/roboto/latin-400.css'
import '@fontsource/roboto/latin-500.css'
import '@fontsource/roboto/latin-700.css'
import '@fontsource/roboto/latin-ext-300.css'
import '@fontsource/roboto/latin-ext-400.css'
import '@fontsource/roboto/latin-ext-500.css'
import '@fontsource/roboto/latin-ext-700.css'
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
import { h } from 'vue'
import { createVuetify } from 'vuetify'
import { aliases, mdi } from 'vuetify/iconsets/mdi-svg'
import { mdiIcons } from './icons'

// SVG icon set: resolves the `mdi-*` names used across the app to the SVG
// paths in icons.js (a tree-shaken subset of @mdi/js). Values that aren't
// in the map — e.g. Vuetify's internal `$` aliases, already resolved to
// SVG paths — are passed through unchanged.
const mdiSvg = {
  component: (props) =>
    h(mdi.component, { ...props, icon: mdiIcons[props.icon] ?? props.icon }),
}

// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
// No global component/directive registration: vite-plugin-vuetify
// (autoImport) injects per-SFC imports at build time, so only the
// components actually used ship in the bundle (JS and CSS). Federated
// plugin remotes must carry their own Vuetify imports (upstream plugin
// builds use the same vite-plugin-vuetify setup).
const savedTheme = typeof localStorage !== 'undefined' ? localStorage.getItem('modoboa_theme') : null
const initialTheme = savedTheme && ['modoboaDark', 'light'].includes(savedTheme) ? savedTheme : 'modoboaDark'
if (typeof document !== 'undefined') {
  document.documentElement.setAttribute('data-theme', initialTheme)
}

export default createVuetify({
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: { mdi: mdiSvg },
  },
  theme: {
    defaultTheme: initialTheme,
    themes: {
      // Editorial dark theme adapted from brunonyland.com. Appearance is
      // entirely frontend-driven (the backend theme API was removed), so
      // these tokens — deep background / surface / text and the accent
      // `primary` — are the single source of truth.
      modoboaDark: {
        dark: true,
        colors: {
          background: '#0a0a0a',
          surface: '#111111',
          'surface-bright': '#1c1c1c',
          'surface-light': '#1a1a1a',
          'surface-variant': '#2a2a2a',
          'on-surface-variant': '#a3a3a3',
          primary: '#7c5cff',
          'primary-lighten-1': '#a594ff',
          'primary-darken-1': '#5a3fd6',
          secondary: '#a594ff',
          'secondary-darken-1': '#7c5cff',
          error: '#ff5b3a',
          info: '#7c5cff',
          success: '#3ddc84',
          warning: '#ffb020',
          label: '#a3a3a3',
          'on-background': '#f0f0f0',
          'on-surface': '#f0f0f0',
          'on-primary': '#0a0a0a',
        },
        variables: {
          'border-color': '#f0f0f0',
          'border-opacity': 0.16,
          'high-emphasis-opacity': 0.95,
          'medium-emphasis-opacity': 0.68,
          'disabled-opacity': 0.4,
          // Stronger hover/focus overlays than the Vuetify defaults
          // (0.04 / 0.12) so interactive states are clearly perceivable —
          // better contrast for accessibility.
          'hover-opacity': 0.12,
          'focus-opacity': 0.16,
        },
      },
      // Light theme option
      light: {
        dark: false,
        colors: {
          background: '#f8f9fa',
          surface: '#ffffff',
          'surface-bright': '#ffffff',
          'surface-light': '#f1f3f5',
          'surface-variant': '#e9ecef',
          'on-surface-variant': '#495057',
          primary: '#7c5cff',
          'primary-lighten-1': '#a594ff',
          'primary-darken-1': '#5a3fd6',
          secondary: '#7c5cff',
          'secondary-darken-1': '#5a3fd6',
          error: '#dc3545',
          info: '#0dcaf0',
          success: '#198754',
          warning: '#fd7e14',
          label: '#6c757d',
          'on-background': '#1a1a1a',
          'on-surface': '#1a1a1a',
          'on-primary': '#ffffff',
        },
        variables: {
          'border-color': '#1a1a1a',
          'border-opacity': 0.12,
          'high-emphasis-opacity': 0.87,
          'medium-emphasis-opacity': 0.60,
          'disabled-opacity': 0.38,
          'hover-opacity': 0.08,
          'focus-opacity': 0.12,
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
      pt_BR: pt,
      ru,
      sv,
      tr,
      zh: zhHans,
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
