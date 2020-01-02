"""Field validators."""

import re

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, URLValidator
from django.utils.translation import ugettext_lazy


class HostnameValidator(object):

    """Validator for fqdn."""

    message = ugettext_lazy("Enter a valid domain name")
    code = "invalid"
    regex = re.compile(URLValidator.host_re)

    def __init__(self, message=None, code=None):
        """Constructor."""
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code

    def __call__(self, value):
        """Check value."""
        if len(value) > 255:
            raise ValidationError(self.message, self.code)
        if value[-1] == ".":
            # strip exactly one dot from the right, if present.
            value = value[:-1]
        if not self.regex.match(value):
            raise ValidationError(self.message, self.code)


validate_hostname = HostnameValidator()


class UTF8EmailValidator(EmailValidator):

    """Validator for addresses using non-ASCII characters."""

    # unicode letters range (must be a unicode string, not a raw string)
    ul = "\u00a1-\uffff"
    ascii_set = "-!#$%&'*+/=?^_`{}|~0-9A-Z"
    user_regex_raw = (
        # dot-atom
        r"^[" + ascii_set + ul + r"]+(\.[" + ascii_set + ul + r"]+)*\Z"
        # quoted-string
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|'
        r'\\[\001-\011\013\014\016-\177])*"\Z)'
    )
    user_regex = re.compile(r"(" + user_regex_raw, re.IGNORECASE)


validate_utf8_email = UTF8EmailValidator()


class UTF8AndEmptyUserEmailValidator(UTF8EmailValidator):

    """Same as upper + allows empty local part."""

    user_regex = re.compile(
        r"(^$|" + UTF8EmailValidator.user_regex_raw, re.IGNORECASE)


validate_utf8_and_empty_user_email = UTF8AndEmptyUserEmailValidator()
