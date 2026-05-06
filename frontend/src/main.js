/**
 * main.js
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

import * as Vue from 'vue'
import * as VueRouter from 'vue-router'
import * as Pinia from 'pinia'
import * as Vuetify from 'vuetify'

// Plugins
import { registerPlugins } from '@/plugins'

// Components
import App from './App.vue'

// Composables
import { createApp } from 'vue'

//api
import repository from '@/api/repository.js'

let globalConfig

fetch(import.meta.env.BASE_URL + 'config.json').then((resp) => {
  resp.json().then((config) => {
    if (!config.API_BASE_URL) {
      throw Error('API_BASE_URL is not defined in config.json')
    }
    globalConfig = config
    repository.defaults.baseURL = config.API_BASE_URL

    const app = createApp(App)

    registerPlugins(app)

    app.mount('#app')

    app.provide('$config', config)
  })
})

export const useGlobalConfig = () => globalConfig

// Expose common packages for plugins
window.__modoboa_libs__ = { Vue, VueRouter, Pinia, Vuetify }
