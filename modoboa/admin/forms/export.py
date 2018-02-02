# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy


class ExportDataForm(forms.Form):
    filename = forms.CharField(
        label=ugettext_lazy("File name"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    sepchar = forms.CharField(
        label=ugettext_lazy("Separator"),
        max_length=1,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    def __init__(self, *args, **kwargs):
        super(ExportDataForm, self).__init__(*args, **kwargs)
        self.fields["sepchar"].widget.attrs = {"class": "col-md-1 form-control"}

    def clean_sepchar(self):
        if self.cleaned_data["sepchar"] == "":
            return ";"
        return self.cleaned_data["sepchar"]

    def clean_filename(self):
        if self.cleaned_data["filename"] == "":
            return self.fields["filename"].initial
        return self.cleaned_data["filename"]


class ExportDomainsForm(ExportDataForm):

    def __init__(self, *args, **kwargs):
        super(ExportDomainsForm, self).__init__(*args, **kwargs)
        self.fields["filename"].initial = "modoboa-domains.csv"


class ExportIdentitiesForm(ExportDataForm):

    def __init__(self, *args, **kwargs):
        super(ExportIdentitiesForm, self).__init__(*args, **kwargs)
        self.fields["filename"].initial = "modoboa-identities.csv"
