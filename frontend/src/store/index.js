import Vue from 'vue'
import Vuex from 'vuex'

import domains from './modules/domains'

Vue.use(Vuex)

const options = {
  modules: {
    domains
  },
  strict: process.env.NODE_ENV !== 'production'
}

export default new Vuex.Store(options)
export { options }
