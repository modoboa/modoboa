"""Custom form fields."""

from django import forms
from django.utils.translation import ugettext_lazy

from . import validators


class DomainNameField(forms.fields.CharField):

    """A subclass of CharField that only accepts a valid domain name."""

    default_error_messages = {
        "invalid": ugettext_lazy("Enter a valid domain name")
    }

    default_validators = [validators.validate_hostname]

    def clean(self, value):
        value = self.to_python(value).strip()
        return super(DomainNameField, self).clean(value)


class UTF8EmailField(forms.fields.EmailField):

    """A subclass of EmailField to support UTF8 addresses."""

    default_validators = [validators.validate_utf8_email]


class UTF8AndEmptyUserEmailField(forms.fields.EmailField):

    """
    A subclass of EmailField to support UTF8 addresses (with or without
    local part).
    """

    default_validators = [validators.validate_utf8_and_empty_user_email]
