"""Forms related to forwards management."""

from django import forms
from django.core import validators
from django.utils.translation import gettext_lazy


class ForwardForm(forms.Form):
    """Forward definition form."""

    dest = forms.CharField(
        label=gettext_lazy("Recipient(s)"),
        widget=forms.Textarea(attrs={"class": "form-control"}),
        required=False,
        help_text=gettext_lazy("Indicate one or more recipients separated by a ','"),
    )
    keepcopies = forms.BooleanField(
        label=gettext_lazy("Keep local copies"),
        required=False,
        help_text=gettext_lazy(
            "Forward messages and store copies into your local mailbox"
        ),
    )

    def clean_dest(self):
        """Check recipients validity."""
        rawdata = self.cleaned_data.get("dest", "").strip()
        recipients = []
        if not rawdata:
            return recipients
        for rcpt in rawdata.split(","):
            validators.validate_email(rcpt)
            recipients += [rcpt]
        return recipients
