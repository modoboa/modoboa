"""Webmail handlers."""

from django.db.models import signals
from django.urls import reverse
from django.dispatch import receiver
from django.utils.translation import gettext as _

from modoboa.admin import models as admin_models
from modoboa.core import signals as core_signals
from modoboa.lib import signals as lib_signals

from . import models


@receiver(core_signals.get_top_notifications)
def check_addressbook_first_sync(sender, include_all, **kwargs):
    """Check if address book first sync has been made."""
    request = lib_signals.get_request()
    qset = request.user.addressbook_set.filter(last_sync__isnull=True)
    condition = (
        not request.user.parameters.get_value("enable_carddav_sync", app="contacts")
        or not qset.exists()
    )
    if condition:
        return []
    return [
        {
            "id": "abook_sync_required",
            "url": reverse("modoboa_contacts:index"),
            "text": _("Your address book must be synced"),
            "level": "warning",
        }
    ]


@receiver(signals.post_save, sender=admin_models.Mailbox)
def create_addressbook(sender, instance, created, **kwargs):
    """Create default address book for new mailbox."""
    if not created:
        return
    models.AddressBook.objects.create(
        user=instance.user, name="Contacts", _path="contacts"
    )


# @receiver(core_signals.extra_static_content)
# def inject_sync_poller(sender, caller, st_type, user, **kwargs):
#     """Inject javascript code."""
#     condition = (
#         caller != "top" or
#         st_type != "js" or
#         not hasattr(user, "mailbox") or
#         not user.parameters.get_value("enable_carddav_sync")
#     )
#     if condition:
#         return ""
#     return """<script>
# $(document).ready(function () {
#     new Poller('%s', {
#         interval: %d * 1000
#     });
# });
# </script>
# """ % (reverse("api:addressbook-sync-from-cdav"),
#        user.parameters.get_value("sync_frequency"))
