# coding: utf-8
from django import forms
from django.utils.translation import ugettext_lazy
from modoboa.lib.parameters import UserParametersForm


class UserSettings(UserParametersForm):
    app = "general"

    lang = forms.ChoiceField(
        initial="en",
        label=ugettext_lazy("Prefered language"),
        choices=[("de", "deutsch"), ("en", "english"),
                ("es", "español"), ("fr", "français"),
                ("pt", "português"), ("sv", "svenska"),],
        help_text=ugettext_lazy("Prefered language to display pages")
    )
