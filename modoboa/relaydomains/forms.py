"""Postfix relay domains extension forms."""

from django import forms
from django.core import validators
from django.utils.translation import ugettext as _

from modoboa.lib.form_utils import WizardStep
from modoboa.lib import validators as lib_validators

from .models import RelayDomain


class RelayDomainWizardStep(WizardStep):

    """A custom wizard step."""

    def check_access(self, wizard):
        """Check if domain is a relay domain."""
        return wizard.steps[0].form.cleaned_data["type"] == "relaydomain"


class RelayDomainFormGeneral(forms.ModelForm):
    """RelayDomain form."""

    class Meta:
        model = RelayDomain
        exclude = ["domain", "creation", "last_modification"]
        widgets = {
            "service": forms.Select(attrs={"class": "form-control"})
        }

    def __init__(self, *args, **kwargs):
        super(RelayDomainFormGeneral, self).__init__(*args, **kwargs)
        self.field_widths = {
            "service": 3
        }

    def clean_target_host(self):
        """Check that target host is valid."""
        validator_list = [
            lib_validators.validate_hostname,
            validators.validate_ipv46_address
        ]
        value = self.cleaned_data.get("target_host")
        for validator in validator_list:
            try:
                validator(value)
            except forms.ValidationError:
                pass
            else:
                return value
        raise forms.ValidationError(_("Invalid value"), code="invalid")

    def save(self, *args, **kwargs):
        """Custom save method."""
        domain = kwargs.get("domain")
        instance = super(RelayDomainFormGeneral, self).save(commit=False)
        if instance.domain and instance.domain.type == "domain":
            # Avoid new creation if domain type has been changed.
            return None
        if domain:
            instance.domain = domain
        if instance.domain.type == "relaydomain":
            instance.save()
        return instance
