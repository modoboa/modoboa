# coding: utf-8
from django import forms
from django.utils.translation import ugettext_lazy
from django.conf import settings
from modoboa.lib.parameters import UserParametersForm
from modoboa.lib.formutils import SeparatorField


def translate_language_code(value):
    if "-" in value:
        return value.split("-")[0]
    return value


class UserSettings(UserParametersForm):
    app = "general"

    sep = SeparatorField(label=ugettext_lazy("Display"))

    lang = forms.ChoiceField(
        initial=translate_language_code(settings.LANGUAGE_CODE),
        label=ugettext_lazy("Prefered language"),
        choices=[("cs", "čeština"), ("de", "deutsch"),
                ("en", "english"), ("es", "español"),
                ("fr", "français"), ("it", "italiano"),
                ("pt", "português"), ("sv", "svenska"),],
        help_text=ugettext_lazy("Prefered language to display pages")
    )
