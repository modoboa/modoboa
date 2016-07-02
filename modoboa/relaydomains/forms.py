"""
Postfix relay domains extension forms.
"""
from django import forms
from django.utils.translation import ugettext_lazy

from modoboa.lib.fields import DomainNameField
from modoboa.lib.form_utils import WizardStep

from .models import RelayDomain


class RelayDomainWizardStep(WizardStep):

    """A custom wizard step."""

    def check_access(self, wizard):
        """Check if domain is a relay domain."""
        return wizard.steps[0].form.cleaned_data["type"] == "relaydomain"


class RelayDomainFormGeneral(forms.ModelForm):

    """RelayDomain form."""

    name = DomainNameField(
        label=ugettext_lazy("Name"),
        help_text=ugettext_lazy("The relay domain name")
    )

    class Meta:
        model = RelayDomain
        exclude = ["domain", "dates"]
        widgets = {
            "service": forms.Select(attrs={"class": "form-control"})
        }

    def __init__(self, *args, **kwargs):
        super(RelayDomainFormGeneral, self).__init__(*args, **kwargs)
        self.field_widths = {
            "service": 3
        }

    def save(self, *args, **kwargs):
        """Custom save method."""
        domain = kwargs.get("domain")
        instance = super(RelayDomainFormGeneral, self).save(commit=False)
        if domain:
            instance.domain = domain
        instance.save()
        return instance
