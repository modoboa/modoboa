"""Custom form fields."""

from django.utils.translation import gettext_lazy

from rest_framework import serializers

from . import validators


class DRFEmailFieldUTF8(serializers.CharField):
    """Custom DRF email field to support UTF8."""

    default_error_messages = {"invalid": gettext_lazy("Enter a valid email address.")}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        validator = validators.UTF8EmailValidator(
            message=self.error_messages["invalid"]
        )
        self.validators.append(validator)


class DRFEmailFieldUTF8AndEmptyUser(serializers.CharField):
    """Custom DRF email field to support UTF8 and empty local part."""

    default_error_messages = {"invalid": gettext_lazy("Enter a valid email address.")}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        validator = validators.UTF8AndEmptyUserEmailValidator(
            message=self.error_messages["invalid"]
        )
        self.validators.append(validator)
