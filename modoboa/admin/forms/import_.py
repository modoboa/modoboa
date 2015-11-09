"""Forms related to import operations."""

from django import forms
from django.utils.translation import ugettext_lazy


class ImportDataForm(forms.Form):

    """Base form to import objects."""

    sourcefile = forms.FileField(label=ugettext_lazy("Select a file"))
    sepchar = forms.CharField(
        label=ugettext_lazy("Separator"),
        max_length=1,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    continue_if_exists = forms.BooleanField(
        label=ugettext_lazy("Continue on error"), required=False,
        help_text=ugettext_lazy("Don't treat duplicated objects as error")
    )

    def __init__(self, *args, **kwargs):
        super(ImportDataForm, self).__init__(*args, **kwargs)
        self.fields["sepchar"].widget.attrs = {"class": "col-md-1 form-control"}

    def clean_sepchar(self):
        if self.cleaned_data["sepchar"] == "":
            return ";"
        return str(self.cleaned_data["sepchar"])


class ImportIdentitiesForm(ImportDataForm):

    """A form to import identities."""

    crypt_password = forms.BooleanField(
        label=ugettext_lazy("Crypt passwords"), required=False,
        help_text=ugettext_lazy(
            "Check this option if passwords contained in your file "
            "are not crypted"
        )
    )
