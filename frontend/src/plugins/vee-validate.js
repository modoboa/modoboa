import Vue from 'vue'
import { ValidationObserver, ValidationProvider, extend } from 'vee-validate'
import { numeric, required } from 'vee-validate/dist/rules'
import { translate } from 'vue-gettext'

const { gettext: $gettext } = translate

// Declare builtin rules here
extend('numeric', {
  ...numeric,
  message: () => $gettext('This field must be a valid number')
})
extend('required', {
  ...required,
  message: () => $gettext('This field is required')
})

// Add custom rules here

// Register components globally
Vue.component('ValidationObserver', ValidationObserver)
Vue.component('ValidationProvider', ValidationProvider)
