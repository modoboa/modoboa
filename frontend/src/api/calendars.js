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
    return repository.get(`/user-calendars/${calendarPk}/accessrules/`)
  },
  createAccessRule(calendarPk, data) {
    return repository.post(`/user-calendars/${calendarPk}/accessrules/`, data)
  },
  updateAccessRule(calendarPk, ruleId, data) {
    return repository.put(
      `/user-calendars/${calendarPk}/accessrules/${ruleId}/`,
      data
    )
  },
  deleteAccessRule(calendarPk, ruleId) {
    return repository.delete(
      `/user-calendars/${calendarPk}/accessrules/${ruleId}/`
    )
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
      data,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    )
  },
  deleteUserEvent(calendarPk, eventId) {
    return repository.delete(`/user-calendars/${calendarPk}/events/${eventId}/`)
  },
  getAttendees() {
    return repository.get('/attendees/')
  },
}
