# -*- coding: utf-8 -*-

"""Forms related to forwards management."""

from __future__ import unicode_literals

from django import forms
from django.core import validators
from django.utils.translation import ugettext_lazy


class ForwardForm(forms.Form):
    """Forward definition form."""

    dest = forms.CharField(
        label=ugettext_lazy("Recipient(s)"),
        widget=forms.Textarea(attrs={"class": "form-control"}),
        required=False,
        help_text=ugettext_lazy(
            "Indicate one or more recipients separated by a ','")
    )
    keepcopies = forms.BooleanField(
        label=ugettext_lazy("Keep local copies"),
        required=False,
        help_text=ugettext_lazy(
            "Forward messages and store copies into your local mailbox")
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
