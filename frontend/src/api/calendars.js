import repository from './repository'

export default {
  getUserCalendars() {
    return repository.get('/user-calendars/')
  },
  getUserCalendar(pk) {
    return repository.get(`/user-calendars/${pk}/`)
  },
  createUserCalendar(data) {
    return repository.post('/user-calendars/', data)
  },
  updateUserCalendar(pk, data) {
    return repository.put(`/user-calendars/${pk}/`, data)
  },
  deleteUserCalendar(pk) {
    return repository.delete(`/user-calendars/${pk}/`)
  },

  getAccessRules(calendarPk) {
    return repository.get('/accessrules/')
  },
  createAccessRule(data) {
    return repository.post('/accessrules/', data)
  },
  updateAccessRule(ruleId, data) {
    return repository.put(`/accessrules/${ruleId}/`, data)
  },
  deleteAccessRule(ruleId) {
    return repository.delete(`/accessrules/${ruleId}/`)
  },

  getUserCalendarEvents(calendarPk, params) {
    return repository.get(`/user-calendars/${calendarPk}/events/`, { params })
  },
  getUserEvent(calendarPk, eventId) {
    return repository.get(`/user-calendars/${calendarPk}/events/${eventId}/`)
  },
  createUserEvent(calendarPk, data) {
    return repository.post(`/user-calendars/${calendarPk}/events/`, data)
  },
  patchUserEvent(calendarPk, eventId, data) {
    return repository.patch(
      `/user-calendars/${calendarPk}/events/${eventId}/`,
      data
    )
  },
  importUserEvents(calendarPk, data) {
    return repository.post(
      `/user-calendars/${calendarPk}/events/import_from_file/`,
      data
    )
  },

  getAttendees() {
    return repository.get('/attendees/')
  },
}
