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

Vue.config.productionTip = false

export const bus = new Vue()

fetch(process.env.BASE_URL + 'config.json').then(resp => {
  resp.json().then((config) => {
    Vue.prototype.$config = config
    new Vue({
      router,
      store,
      vuetify,
      render: h => h(App)
    }).$mount('#app')
  })
})
