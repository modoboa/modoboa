"""Contacts forms."""

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from modoboa.lib import cryptutils
from modoboa.lib import form_utils
from modoboa.lib import signals as lib_signals
from modoboa.parameters import forms as param_forms

from . import tasks


class UserSettings(param_forms.UserParametersForm):
    """User settings."""

    app = "contacts"

    sep1 = form_utils.SeparatorField(label=_("Synchronization"))

    enable_carddav_sync = form_utils.YesNoField(
        initial=False,
        label=_("Synchonize address book using CardDAV"),
        help_text=_(
            "Choose to synchronize or not your address book using CardDAV. "
            "You will be able to access your contacts from the outside."
        ),
    )

    sync_frequency = forms.IntegerField(
        initial=300,
        label=_("Synchronization frequency"),
        help_text=_("Interval in seconds between 2 synchronization requests"),
    )

    visibility_rules = {"sync_frequency": "enable_carddav_sync=True"}

    def clean_sync_frequency(self):
        """Make sure frequency is a positive integer."""
        if self.cleaned_data["sync_frequency"] < 60:
            raise forms.ValidationError(_("Minimum allowed value is 60s"))
        return self.cleaned_data["sync_frequency"]

    def save(self, *args, **kwargs):
        """Create remote cal if necessary."""
        super(UserSettings, self).save(*args, **kwargs)
        if not self.cleaned_data["enable_carddav_sync"]:
            return
        abook = self.user.addressbook_set.first()
        if abook.last_sync:
            return
        request = lib_signals.get_request()
        tasks.create_cdav_addressbook(
            abook, cryptutils.decrypt(request.session["password"])
        )
        if not abook.contact_set.exists():
            abook.last_sync = timezone.now()
            abook.save(update_fields=["last_sync"])
