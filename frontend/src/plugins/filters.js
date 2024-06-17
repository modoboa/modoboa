import gettext from './gettext'
import { DateTime } from 'luxon'

const { $gettext } = gettext

export default {
  install: (app) => {
    app.config.globalProperties.$yesno = (value) => {
      return value ? $gettext('yes') : $gettext('no')
    }
    app.config.globalProperties.$date = (value) => {
      return DateTime.fromISO(value)
        .setLocale(gettext.current)
        .toLocaleString(DateTime.DATETIME_MED)
    }
    app.config.globalProperties.$truncate = (value, length, clamp) => {
      clamp = clamp || '...'
      return value.length > length ? value.slice(0, length) + clamp : value
    }
  },
}
