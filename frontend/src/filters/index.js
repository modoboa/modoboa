import Vue from 'vue'
import { translate } from 'vue-gettext'
const { gettext: $gettext } = translate

Vue.filter('yesno', function (value) {
  return (value) ? $gettext('yes') : $gettext('no')
})
