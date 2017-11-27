"""Postfix relay domains extension forms."""

from __future__ import unicode_literals

from django import forms

from modoboa.lib.form_utils import WizardStep
from modoboa.transport import backends as tr_backends
from modoboa.transport import forms as tr_forms
from modoboa.transport import models as tr_models


class RelayDomainWizardStep(WizardStep):

    """A custom wizard step."""

    def check_access(self, wizard):
        """Check if domain is a relay domain."""
        return wizard.steps[0].form.cleaned_data["type"] == "relaydomain"


class RelayDomainFormGeneral(tr_forms.BackendSettingsMixin, forms.ModelForm):
    """A form to display transport of type relay."""

    class Meta(object):
        model = tr_models.Transport
        exclude = [
            "creation", "pattern", "service", "next_hop", "enabled",
            "_settings"
        ]

    def __init__(self, *args, **kwargs):
        super(RelayDomainFormGeneral, self).__init__(*args, **kwargs)
        settings = tr_backends.manager.get_backend_settings("relay")
        self.inject_backend_settings("relay", settings)

    def clean(self):
        """Check values."""
        cleaned_data = super(RelayDomainFormGeneral, self).clean()
        if self.errors:
            return cleaned_data
        self.clean_backend_fields("relay")
        return cleaned_data

    def save(self, *args, **kwargs):
        """Custom save method."""
        domain = kwargs.pop("domain", None)
        if domain.type != "relaydomain":
            # We don't want to recreate the transport we just deleted
            # (post_save signal).
            return None
        instance = super(RelayDomainFormGeneral, self).save(commit=False)
        instance.pattern = domain.name
        instance.service = "relay"
        instance.enabled = domain.enabled
        self.backend.serialize(instance)
        instance.save()
        return instance
