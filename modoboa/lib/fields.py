# -*- coding: utf-8 -*-

"""Custom form fields."""

from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy

from rest_framework import serializers

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


class DRFEmailFieldUTF8(serializers.CharField):
    """Custom DRF email field to support UTF8."""

    default_error_messages = {
        "invalid": ugettext_lazy("Enter a valid email address.")
    }

    def __init__(self, **kwargs):
        super(DRFEmailFieldUTF8, self).__init__(**kwargs)
        validator = validators.UTF8EmailValidator(
            message=self.error_messages["invalid"])
        self.validators.append(validator)


class DRFEmailFieldUTF8AndEmptyUser(serializers.CharField):
    """Custom DRF email field to support UTF8 and empty local part."""

    default_error_messages = {
        "invalid": ugettext_lazy("Enter a valid email address.")
    }

    def __init__(self, **kwargs):
        super(DRFEmailFieldUTF8AndEmptyUser, self).__init__(**kwargs)
        validator = validators.UTF8AndEmptyUserEmailValidator(
            message=self.error_messages["invalid"])
        self.validators.append(validator)
