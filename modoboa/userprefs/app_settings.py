# coding: utf-8
from django import forms
from django.utils.translation import ugettext_lazy
from django.conf import settings
from modoboa.lib.parameters import UserParametersForm


def translate_language_code(value):
    if "-" in value:
        return value.split("-")[0]
    return value


class UserSettings(UserParametersForm):
    app = "general"

    lang = forms.ChoiceField(
        initial=translate_language_code(settings.LANGUAGE_CODE),
        label=ugettext_lazy("Prefered language"),
        choices=[("de", "deutsch"), ("en", "english"),
                ("es", "español"), ("fr", "français"),
                ("pt", "português"), ("sv", "svenska"),],
        help_text=ugettext_lazy("Prefered language to display pages")
    )
