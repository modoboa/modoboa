/**
 * main.js
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Plugins
import { registerPlugins } from '@/plugins'

// Components
import App from './App.vue'

// Composables
import { createApp } from 'vue'

//api
import repository from '@/api/repository.js'

fetch(import.meta.env.BASE_URL + 'config.json').then((resp) => {
    resp.json().then((config) => {
        if (!config.API_BASE_URL) {
            throw Error('API_BASE_URL is not defined in config.json')
        }
        repository.defaults.baseURL = config.API_BASE_URL

        const app = createApp(App)

        registerPlugins(app)

        app.mount('#app')

        app.provide('$config', config)
    })
})
