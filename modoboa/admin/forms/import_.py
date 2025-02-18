"""Forms related to import operations."""

from django import forms
from django.utils.translation import gettext_lazy


class ImportDataForm(forms.Form):
    """Base form to import objects."""

    sourcefile = forms.FileField(label=gettext_lazy("Select a file"))
    sepchar = forms.CharField(
        label=gettext_lazy("Separator"),
        max_length=1,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    continue_if_exists = forms.BooleanField(
        label=gettext_lazy("Continue on error"),
        required=False,
        help_text=gettext_lazy("Don't treat duplicated objects as error"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sepchar"].widget.attrs = {"class": "col-md-1 form-control"}

    def clean_sepchar(self):
        if self.cleaned_data["sepchar"] == "":
            return ";"
        return self.cleaned_data["sepchar"]


class ImportIdentitiesForm(ImportDataForm):
    """A form to import identities."""

    crypt_password = forms.BooleanField(
        label=gettext_lazy("Crypt passwords"),
        required=False,
        help_text=gettext_lazy(
            "Check this option if passwords contained in your file " "are not crypted"
        ),
    )
