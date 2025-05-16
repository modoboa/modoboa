"""Core forms."""

import oath

from django import forms
from django.contrib.auth import forms as auth_forms, get_user_model
from django.db.models import Q
from django.utils.translation import gettext as _, gettext_lazy

import django_otp

from modoboa.lib.form_utils import UserKwargModelFormMixin


class AuthenticationForm(auth_forms.AuthenticationForm):

    rememberme = forms.BooleanField(initial=False, required=False)


class PasswordResetForm(auth_forms.PasswordResetForm):
    """Custom password reset form."""

    def get_users(self, email):
        """Return matching user(s) who should receive a reset."""
        return (
            get_user_model()
            ._default_manager.filter(email__iexact=email, is_active=True)
            .exclude(Q(secondary_email__isnull=True) | Q(secondary_email=""))
        )

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """Send message to secondary email instead."""
        to_email = context["user"].secondary_email
        super().send_mail(
            subject_template_name,
            email_template_name,
            context,
            from_email,
            to_email,
            html_email_template_name,
        )


class VerifySMSCodeForm(forms.Form):
    """A form to verify a code received by SMS."""

    code = forms.CharField(
        label=gettext_lazy("Verification code"),
        widget=forms.widgets.TextInput(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        self.totp_secret = kwargs.pop("totp_secret")
        super().__init__(*args, **kwargs)

    def clean_code(self):
        code = self.cleaned_data["code"]
        if not oath.accept_totp(self.totp_secret, code)[0]:
            raise forms.ValidationError(_("Invalid code"))
        return code


class Verify2FACodeForm(UserKwargModelFormMixin, forms.Form):
    """A form to verify 2FA codes validity."""

    next = forms.CharField(required=False)
    tfa_code = forms.CharField()

    def clean_tfa_code(self):
        code = self.cleaned_data["tfa_code"]
        device = django_otp.match_token(self.user, code)
        if device is None:
            raise forms.ValidationError(_("This code is invalid"))
        return device
