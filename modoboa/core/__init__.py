
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from modoboa.lib import events


PERMISSIONS = {
    "SimpleUsers": [],
    "DomainAdmins": [
        ["core", "user", "add_user"],
        ["core", "user", "change_user"],
        ["core", "user", "delete_user"],
        ["admin", "domain", "view_domains"],
        ["admin", "domain", "view_domain"],
        ["admin", "mailbox", "add_mailbox"],
        ["admin", "mailbox", "change_mailbox"],
        ["admin", "mailbox", "delete_mailbox"],
        ["admin", "alias", "add_alias"],
        ["admin", "alias", "change_alias"],
        ["admin", "alias", "delete_alias"],
        ["admin", "mailbox", "view_mailboxes"],
        ["admin", "alias", "view_aliases"],
    ],
    "Resellers": [
        ["core", "user", "add_user"],
        ["core", "user", "change_user"],
        ["core", "user", "delete_user"],
        ["admin", "domain", "view_domains"],
        ["admin", "domain", "view_domain"],
        ["admin", "mailbox", "add_mailbox"],
        ["admin", "mailbox", "change_mailbox"],
        ["admin", "mailbox", "delete_mailbox"],
        ["admin", "alias", "add_alias"],
        ["admin", "alias", "change_alias"],
        ["admin", "alias", "delete_alias"],
        ["admin", "mailbox", "view_mailboxes"],
        ["admin", "alias", "view_aliases"],
        ["admin", "domain", "view_domains"],
        ["admin", "domain", "add_domain"],
        ["admin", "domain", "change_domain"],
        ["admin", "domain", "delete_domain"],
        ["admin", "domainalias", "add_domainalias"],
        ["admin", "domainalias", "change_domainalias"],
        ["admin", "domainalias", "delete_domainalias"],
    ]
}


@events.observe("TopNotifications")
def check_for_new_versions(request, include_all):
    """Check if new versions are available."""
    from modoboa.core.utils import check_for_updates

    if not request.user.is_superuser:
        return []
    status, extensions = check_for_updates(request)
    if not status:
        return [{"id": "newversionavailable"}] if include_all else []
    return [{
        "id": "newversionavailable",
        "url": reverse("core:index") + "#info/",
        "text": _("One or more updates are available"),
        "level": "info",
    }]

default_app_config = "modoboa.core.apps.CoreConfig"
