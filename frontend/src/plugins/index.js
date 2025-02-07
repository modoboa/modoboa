/**
 * plugins/index.js
 *
 * Automatically included in `./src/main.js`
 */

// Plugins
import vuetify from './vuetify'
import router from '../router'
import gettext from './gettext'
import filters from './filters'
import permissions from './permissions'
import pinia from '@/stores'
import VueApexCharts from 'vue3-apexcharts'

export function registerPlugins(app) {
  app
    .use(gettext)
    .use(vuetify)
    .use(pinia)
    .use(router)
    .use(filters)
    .use(permissions)
    .use(VueApexCharts)
}
