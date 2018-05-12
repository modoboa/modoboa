# -*- coding: utf-8 -*-

"""Postfix relay domains extension forms."""

from __future__ import unicode_literals

from django.db.models.signals import pre_save, post_save

from modoboa.lib.form_utils import WizardStep
from modoboa.transport import forms as tr_forms, models as tr_models


class DisableSignals(object):
    """Context manager to disable signals."""

    def __init__(self):
        self.stashed_signals = {}
        self.disabled_signals = [pre_save, post_save]

    def __enter__(self):
        for signal in self.disabled_signals:
            self.disconnect(signal)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for signal in list(self.stashed_signals.keys()):
            self.reconnect(signal)

    def disconnect(self, signal):
        self.stashed_signals[signal] = signal.receivers
        signal.receivers = []

    def reconnect(self, signal):
        signal.receivers = self.stashed_signals.get(signal, [])
        del self.stashed_signals[signal]


class RelayDomainWizardStep(WizardStep):
    """A custom wizard step."""

    def check_access(self, wizard):
        """Check if domain is a relay domain."""
        return wizard.steps[0].form.cleaned_data["type"] == "relaydomain"


class RelayDomainFormGeneral(tr_forms.TransportForm):
    """A form to display transport."""

    class Meta:
        model = tr_models.Transport
        exclude = [
            "creation", "pattern", "next_hop", "enabled",
            "_settings"
        ]

    def save(self, *args, **kwargs):
        """Custom save method."""
        domain = kwargs.pop("domain", None)
        if domain.type != "relaydomain":
            # We don't want to recreate the transport we just deleted it
            # (post_save signal).
            return None
        instance = super(RelayDomainFormGeneral, self).save()
        instance.pattern = domain.name
        instance.save()
        if not domain.transport:
            domain.transport = instance
            with DisableSignals():
                domain.save(update_fields=["transport"])
        return instance
