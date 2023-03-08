import Vue from 'vue'
import Vuex from 'vuex'

import auth from '@/store/modules/auth'
import domains from '@/store/modules/domains'
import identities from '@/store/modules/identities'
import providers from '@/store/modules/providers'

Vue.use(Vuex)

export default new Vuex.Store({
  modules: {
    auth,
    domains,
    identities,
    providers
  },
  strict: process.env.NODE_ENV !== 'production'
})
