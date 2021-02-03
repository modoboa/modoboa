import Vue from 'vue'
import './plugins/axios'
import './plugins/vee-validate'
import './plugins/vue-cookie'
import './plugins/vue-gettext'
import './filters'
import App from './App.vue'
import router from './router'
import store from './store'
import vuetify from './plugins/vuetify'

Vue.config.productionTip = false

export const bus = new Vue()

new Vue({
  router,
  store,
  vuetify,
  render: h => h(App)
}).$mount('#app')
