"""Custom password validators."""

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _, ungettext


class ComplexityValidator(object):
    """Check password contains at least a few things."""

    def __init__(self, upper=1, lower=1, digits=1, specials=1):
        self.upper = upper
        self.lower = lower
        self.digits = digits
        self.specials = specials

    def validate(self, password, user=None):
        special_characters = "~!@#$%^&*()_+{}\":;,'[]"
        condition = (
            self.digits > 0 and
            sum(1 for char in password if char.isdigit()) < self.digits)
        if condition:
            raise ValidationError(
                ungettext(
                    "Password must contain at least {} digit.",
                    "Password must contain at least {} digits.",
                    self.digits
                ).format(self.digits))
        condition = (
            self.lower > 0 and
            sum(1 for char in password if char.islower()) < self.lower)
        if condition:
            raise ValidationError(
                ungettext(
                    "Password must contain at least {} lowercase letter.",
                    "Password must contain at least {} lowercase letters.",
                    self.lower
                )
                .format(self.lower))
        condition = (
            self.upper > 0 and
            sum(1 for char in password if char.isupper()) < self.upper)
        if condition:
            raise ValidationError(
                ungettext(
                    "Password must contain at least {} uppercase letter.",
                    "Password must contain at least {} uppercase letters.",
                    self.upper
                )
                .format(self.upper))
        condition = (
            self.specials > 0 and
            sum(1 for char in password if char in special_characters) <
            self.specials)
        if condition:
            raise ValidationError(
                ungettext(
                    "Password must contain at least {} special character.",
                    "Password must contain at least {} special characters.",
                    self.specials
                )
                .format(self.specials))

    def get_help_text(self):
        return _(
            "Your password must contain a combination of different "
            "character types.")
