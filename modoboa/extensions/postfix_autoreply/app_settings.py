# coding: utf-8
from django.utils.translation import ugettext_lazy
from django import forms
from modoboa.lib.parameters import AdminParametersForm
from modoboa.lib.formutils import SeparatorField


class ParametersForm(AdminParametersForm):
    app = "postfix_autoreply"

    general_sep = SeparatorField(label=ugettext_lazy("General"))

    autoreplies_timeout = forms.IntegerField(
        label=ugettext_lazy("Automatic reply timeout"),
        initial=86400,
        help_text=ugettext_lazy("Timeout in seconds between two auto-replies to the same recipient")
    )

