# coding: utf-8
from django.utils.translation import ugettext_lazy as _
from django import forms
from sievelib.managesieve import SUPPORTED_AUTH_MECHS
from modoboa.lib.parameters import AdminParametersForm, UserParametersForm
from modoboa.lib.formutils import SeparatorField, YesNoField, InlineRadioSelect


def supported_auth_mechs():
    values = [('AUTO', 'auto')]
    for m in SUPPORTED_AUTH_MECHS:
        values += [(m, m.lower())]
    return values


class ParametersForm(AdminParametersForm):
    app = "sievefilters"

    sep1 = SeparatorField(label=_("ManageSieve settings"))

    server = forms.CharField(
        label=_("Server address"),
        initial="127.0.0.1",
        help_text=_("Address of your MANAGESIEVE server"),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    port = forms.IntegerField(
        label=_("Server port"),
        initial=4190,
        help_text=_("Listening port of your MANAGESIEVE server"),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    starttls = YesNoField(
        label=_("Connect using STARTTLS"),
        initial="no",
        help_text=_("Use the STARTTLS extension")
    )

    authentication_mech = forms.ChoiceField(
        label=_("Authentication mechanism"),
        choices=supported_auth_mechs(),
        initial="auto",
        help_text=_("Prefered authentication mechanism"),
        widget=forms.Select(attrs={"class": "form-control"})
    )


class UserSettings(UserParametersForm):
    app = "sievefilters"

    sep1 = SeparatorField(label=_("General"))

    editor_mode = forms.ChoiceField(
        initial="gui",
        label=_("Editor mode"),
        choices=[("raw", "raw"), ("gui", "simplified")],
        help_text=_("Select the mode you want the editor to work in"),
        widget=InlineRadioSelect(attrs={"type": "checkbox"})
    )

    @staticmethod
    def has_access(user):
        return user.mailbox_set.count() != 0
