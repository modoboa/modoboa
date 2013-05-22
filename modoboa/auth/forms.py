# coding: utf-8
from django import forms
from django.utils.translation import ugettext_lazy as _

class LoginForm(forms.Form):
    username = forms.CharField(
        label=_("Username"),
        widget=forms.TextInput(attrs={"class": "input-block-level"})
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={"class": "input-block-level"})
    )
    rememberme = forms.BooleanField(
        initial=False,
        required=False
    )
