"""Core forms."""

import oath

from django import forms
from django.contrib.auth import forms as auth_forms, get_user_model, password_validation
from django.db.models import Q
from django.utils.translation import gettext as _, gettext_lazy

import django_otp

from modoboa.core.models import User, UserFidoKey
from modoboa.lib.form_utils import UserKwargModelFormMixin
from modoboa.parameters import tools as param_tools


class AuthenticationForm(auth_forms.AuthenticationForm):

    rememberme = forms.BooleanField(initial=False, required=False)


class ProfileForm(forms.ModelForm):
    """Form to update User profile."""

    oldpassword = forms.CharField(
        label=gettext_lazy("Old password"),
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    newpassword = forms.CharField(
        label=gettext_lazy("New password"),
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    confirmation = forms.CharField(
        label=gettext_lazy("Confirmation"),
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "language",
            "phone_number",
            "secondary_email",
        )
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, update_password, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not update_password:
            del self.fields["oldpassword"]
            del self.fields["newpassword"]
            del self.fields["confirmation"]

    def clean_oldpassword(self):
        if self.cleaned_data["oldpassword"] == "":
            return self.cleaned_data["oldpassword"]

        if param_tools.get_global_parameter("authentication_type") != "local":
            return self.cleaned_data["oldpassword"]

        if not self.instance.check_password(self.cleaned_data["oldpassword"]):
            raise forms.ValidationError(_("Old password mismatchs"))
        return self.cleaned_data["oldpassword"]

    def clean(self):
        super().clean()
        if self.errors:
            return self.cleaned_data
        oldpassword = self.cleaned_data.get("oldpassword")
        newpassword = self.cleaned_data.get("newpassword")
        confirmation = self.cleaned_data.get("confirmation")
        if newpassword and confirmation:
            if oldpassword:
                if newpassword != confirmation:
                    self.add_error("confirmation", _("Passwords mismatch"))
                else:
                    try:
                        password_validation.validate_password(
                            confirmation, self.instance
                        )
                    except forms.ValidationError as err:
                        self.add_error("confirmation", err)
            else:
                self.add_error("oldpassword", _("This field is required."))
        elif newpassword or confirmation:
            if not confirmation:
                self.add_error("confirmation", _("This field is required."))
            else:
                self.add_error("newpassword", _("This field is required."))
        return self.cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            if self.cleaned_data.get("confirmation", "") != "":
                user.set_password(
                    self.cleaned_data["confirmation"], self.cleaned_data["oldpassword"]
                )
            user.save()
        return user


class TwoFAChoiceForm(forms.Form):
    """Form to select the 2FA method of choice."""

    two_fa_choices = forms.ChoiceField(choices=(), required=True)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        fido_keys = UserFidoKey.objects.filter(user=user)
        if fido_keys.exists():
            self.fields["two_fa_choices.choices"].choices = [
                ("TOTP", "TOTP or recovery codes"),
                ("FIDO", "Webauthn device"),
            ]


class APIAccessForm(forms.Form):
    """Form to control API access."""

    enable_api_access = forms.BooleanField(
        label=gettext_lazy("Enable API access"), required=False
    )

    def __init__(self, *args, **kwargs):
        """Initialize form."""
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["enable_api_access"].initial = hasattr(user, "auth_token")


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
