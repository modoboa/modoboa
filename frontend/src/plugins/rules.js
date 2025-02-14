import gettext from './gettext'

const { $gettext } = gettext

function validateEmail(email) {
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return $gettext('Not a valid email')
  } else {
    return true
  }
}

function validateNumeric(value) {
  if (isNaN(value)) {
    return false
  }
  var x = parseFloat(value)
  return (x | 0) === x
}

function samePassword(value, confirmation) {
  return value === confirmation
}

export default {
  required: (value) =>
    (value !== '' &&
      value != null &&
      value !== undefined &&
      (!Array.isArray(value) || value.length)) ||
    $gettext('Field is required'),
  email: (value) => validateEmail(value),
  emailOrNull: (value) => value != null || value !== '' || validateEmail(value),
  minLength: (len) => (value) =>
    value.length > len ||
    $gettext('Minimum length is %{ length }', { length: len }),
  numericOrNull: (value) =>
    value == null ||
    value === '' ||
    validateNumeric(value) ||
    $gettext('Must be a numeric value or empty'),
  samePassword: (value, confirmation) =>
    samePassword(value, confirmation) || $gettext('Passwords mismatch'),
  portNumber: (value) =>
    (value > 0 && value < 65536) || $gettext('Invalid port number'),
}
