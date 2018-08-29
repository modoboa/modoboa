import Vue from 'vue'
/* import Buefy from 'buefy'
 * import 'buefy/lib/buefy.css'
 * import '@mdi/font/css/materialdesignicons.css'
 * */
import Vuetify from 'vuetify'
import Cookies from 'js-cookie'
import 'vuetify/dist/vuetify.min.css'
import 'material-design-icons-iconfont/dist/material-design-icons.css'
import App from './App'
import router from './router'
import store from './store'

// Vue.use(Buefy)
Vue.use(Vuetify)

Vue.config.productionTip = false

/* Deal with django CSRF protection */
let csrftoken = Cookies.get('csrftoken')
Vue.http.headers.common['X-CSRFTOKEN'] = csrftoken

/* eslint-disable no-new */
new Vue({
    el: '#app',
    router,
    store,
    components: { App },
    template: '<App/>'
})
