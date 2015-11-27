# coding: utf-8

"""Core forms."""

from django import forms
from django.utils.translation import ugettext as _, ugettext_lazy

from passwords.fields import PasswordField

from modoboa.core.models import User
from modoboa.lib import parameters


class LoginForm(forms.Form):

    """User login form."""

    username = forms.CharField(
        label=ugettext_lazy("Username"),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    password = forms.CharField(
        label=ugettext_lazy("Password"),
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    rememberme = forms.BooleanField(
        initial=False,
        required=False
    )


class ProfileForm(forms.ModelForm):

    """Form to update User profile."""

    oldpassword = forms.CharField(
        label=ugettext_lazy("Old password"), required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    newpassword = PasswordField(
        label=ugettext_lazy("New password"), required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    confirmation = PasswordField(
        label=ugettext_lazy("Confirmation"), required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "language",
                  "phone_number", "secondary_email")
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'})
        }

    def __init__(self, update_password, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        if not update_password:
            del self.fields["oldpassword"]
            del self.fields["newpassword"]
            del self.fields["confirmation"]

    def clean_oldpassword(self):
        if self.cleaned_data["oldpassword"] == "":
            return self.cleaned_data["oldpassword"]

        if parameters.get_admin("AUTHENTICATION_TYPE") != "local":
            return self.cleaned_data["oldpassword"]

        if not self.instance.check_password(self.cleaned_data["oldpassword"]):
            raise forms.ValidationError(_("Old password mismatchs"))
        return self.cleaned_data["oldpassword"]

    def clean_confirmation(self):
        newpassword = self.cleaned_data["newpassword"]
        confirmation = self.cleaned_data["confirmation"]
        if newpassword != confirmation:
            raise forms.ValidationError(_("Passwords mismatch"))
        return self.cleaned_data["confirmation"]

    def save(self, commit=True):
        user = super(ProfileForm, self).save(commit=False)
        if commit:
            if self.cleaned_data.get("confirmation", "") != "":
                user.set_password(
                    self.cleaned_data["confirmation"],
                    self.cleaned_data["oldpassword"]
                )
            user.save()
        return user


class APIAccessForm(forms.Form):

    """Form to control API access."""

    enable_api_access = forms.BooleanField(
        label=_("Enable API access"), required=False)

    def __init__(self, *args, **kwargs):
        """Initialize form."""
        user = kwargs.pop("user")
        super(APIAccessForm, self).__init__(*args, **kwargs)
        self.fields["enable_api_access"].initial = hasattr(user, "auth_token")
