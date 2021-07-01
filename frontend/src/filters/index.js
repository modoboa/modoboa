import Vue from 'vue'
import { DateTime } from 'luxon'
import { translate } from 'vue-gettext'
const { gettext: $gettext } = translate

Vue.filter('yesno', function (value) {
  return (value) ? $gettext('yes') : $gettext('no')
})

/*
** Return a human readable version of the given date string.
*/
Vue.filter('date', function (value) {
  return DateTime.fromISO(value).setLocale('en').toLocaleString(DateTime.DATETIME_MED)
})

/*
** Truncate given string.
*/
Vue.filter('truncate', function (text, length, clamp) {
  clamp = clamp || '...'
  return text.length > length ? text.slice(0, length) + clamp : text
})
