"""Custom form validators."""

from email.utils import getaddresses

from django.utils.encoding import force_text
from django.core.validators import validate_email


class EmailListValidator(object):

    """Validate a comma separated list of email."""

    def __call__(self, value):
        value = force_text(value)
        emails = [unicode.strip(email) for email in value.split(",")]
        addresses = getaddresses(emails)
        [validate_email(e) for r, e in addresses.values]

validate_email_list = EmailListValidator()

