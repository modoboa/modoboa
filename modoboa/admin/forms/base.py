"""Custom form tools."""

import re

from django.core.validators import EmailValidator
from django.forms.fields import EmailField as OriginalEmailField


class CustomEmailValidator(EmailValidator):

    """Allow empty user_part."""

    user_regex = re.compile(
        r"(^$"
        r"|^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*\Z"  # dot-atom
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"\Z)',  # quoted-string
        re.IGNORECASE)

validate_email = CustomEmailValidator()


class EmailField(OriginalEmailField):

    """A field that accepts email addresses."""

    default_validators = [validate_email]
