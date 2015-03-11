from django.utils.encoding import force_text
from django.utils.deconstruct import deconstructible
from django.core.validators import validate_email
from email.utils import getaddresses

class EmailListValidator(object):
    """
    Validate a comma separated list of email
    """
    def __call__(self, value):
        value = force_text(value)
        emails = map(unicode.strip, value.split(','))
        addresses = getaddresses(emails)
        [ validate_email(e) for r, e in addresses ]

validate_email_list = EmailListValidator()

