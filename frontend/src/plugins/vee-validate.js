import Vue from 'vue'
import { ValidationObserver, ValidationProvider, extend } from 'vee-validate'
import { confirmed, email, numeric, required } from 'vee-validate/dist/rules'
import { translate } from 'vue-gettext'
import account from '@/api/account'

const { gettext: $gettext } = translate

// Declare builtin rules here
extend('samePassword', {
  ...confirmed,
  message: () => $gettext('Passwords mismatch')
})
extend('numeric', {
  ...numeric,
  message: () => $gettext('This field must be a valid number')
})
extend('required', {
  ...required,
  message: () => $gettext('This field is required')
})
extend('email', {
  ...email,
  message: () => $gettext('Specify an email address')
})

// Add custom rules here
extend('validPassword', {
  validate: async (value) => {
    try {
      await account.checkPassword(value)
      return true
    } catch (error) {
      return false
    }
  },
  message: $gettext('Invalid password')
})
extend('portNumber', {
  validate: async (value) => {
    if (value < 0 || value > 65535) {
      return false
    }
    return true
  },
  message: $gettext('Specify a valid port number')
})

// Register components globally
Vue.component('ValidationObserver', ValidationObserver)
Vue.component('ValidationProvider', ValidationProvider)
