"""Export related forms."""

from django import forms
from django.utils.translation import ugettext_lazy


class ExportDataForm(forms.Form):
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
