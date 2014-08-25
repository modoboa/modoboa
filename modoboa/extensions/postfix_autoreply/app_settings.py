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
        help_text=ugettext_lazy("Timeout in seconds between two auto-replies to the same recipient"),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    default_subject = forms.CharField(
        label=ugettext_lazy("Default subject"),
        initial=ugettext_lazy("I'm off"),
        help_text=ugettext_lazy(
            "Default subject used when an auto-reply message is created automatically"
        ),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    default_content = forms.CharField(
        label=ugettext_lazy("Default content"),
        initial=ugettext_lazy(
            """I'm currently off. I'll answer as soon as I come back.

Best regards,
%(name)s
"""),
        help_text=ugettext_lazy(
            "Default content used when an auto-reply message is created "
            "automatically. The '%(name)s' macro will be replaced by the "
            "user's full name."
        ),
        widget=forms.widgets.Textarea(attrs={"class": "form-control"})
    )

    def clean_default_content(self):
        """Check if the provided value is valid.

        Must be a valid format string which will be used with the %
        operator.
        """
        tpl = self.cleaned_data["default_content"]
        try:
            test = tpl % {"name": "Antoine Nguyen"}
        except (KeyError, ValueError):
            raise forms.ValidationError(ugettext_lazy("Invalid syntax"))
        return tpl
