import Vue from 'vue'
import './plugins/vee-validate'
import './plugins/vue-cookie'
import './plugins/vue-gettext'
import './filters'
import App from './App.vue'
import router from './router'
import store from './store'
import vuetify from './plugins/vuetify'
import sassStyles from './styles/global.scss' // eslint-disable-line no-unused-vars
import repository from './api/repository'

Vue.config.productionTip = false

export const bus = new Vue()

fetch(process.env.BASE_URL + 'config.json').then(resp => {
  resp.json().then((config) => {
    if (!config.API_BASE_URL) {
      throw Error('API_BASE_URL is not defined in config.json')
    }
    repository.defaults.baseURL = config.API_BASE_URL

    Vue.prototype.$config = config

    new Vue({
      router,
      store,
      vuetify,
      render: h => h(App)
    }).$mount('#app')
  })
})
