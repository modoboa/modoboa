import Vue from 'vue'
import Vuetify from 'vuetify/lib'

import DomainIcon from '@/components/icons/DomainIcon'

Vue.use(Vuetify)

export default new Vuetify({
  theme: {
    themes: {
      light: {
        primary: '#046BF8',
        secondary: '#F18429'
      }
    }
  },
  icons: {
    values: {
      domain: {
        component: DomainIcon
      }
    }
  }
})
