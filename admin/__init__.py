# -*- coding: utf-8 -*-

from modoboa.lib import parameters, events
from django.utils.translation import ugettext as _, ugettext_lazy
from django.db.utils import DatabaseError
from models import Extension

parameters.register_admin("AUTHENTICATION_TYPE", type="list", deflt="local",
                          values=[('local', ugettext_lazy("Local")),
                                  ('ldap', "LDAP")],
                          help=ugettext_lazy("The backend used for authentication"))
parameters.register_admin("CREATE_DIRECTORIES", type="list_yesno", deflt="yes",
			  help=ugettext_lazy("Modoboa will handle mailbox creation on filesystem"))
parameters.register_admin("STORAGE_PATH", type="string", deflt="/var/vmail",
                          help=ugettext_lazy("Path to the root directory where messages are stored"))
parameters.register_admin("VIRTUAL_UID", type="string", deflt="vmail",
                          help=ugettext_lazy("UID of the virtual user which owns domains/mailboxes/messages on the filesystem"))
parameters.register_admin("VIRTUAL_GID", type="string", deflt="vmail",
                          help=ugettext_lazy("GID of the virtual user which owns domains/mailboxes/messages on the filesystem"))
parameters.register_admin("MAILBOX_TYPE", type="list", deflt="maildir",
                          values=[("maildir", "maildir"), ("mbox", "mbox")],
                          help=ugettext_lazy("Mailboxes storage format"))
parameters.register_admin("MAILDIR_ROOT", type="string", deflt=".maildir",
                          help=ugettext_lazy("Sub-directory (inside the mailbox) where messages are stored when using the maildir format"))
parameters.register_admin(
    "PASSWORD_SCHEME", type="list", deflt="crypt",
    values=[("crypt", "crypt"), ("md5", "md5"), ("sha256", "sha256"), ("plain", "plain")],
    help=ugettext_lazy("Scheme used to crypt mailbox passwords")
    )
parameters.register_admin("ITEMS_PER_PAGE", type="int", deflt=30,
                          help=ugettext_lazy("Number of displayed items per page"))

def enabled_applications():
    """Return the list of currently enabled extensions

    We check if the table exists before trying to fetch activated
    extensions because the admin module is always imported by Django,
    even before the database exists (example: the first ``syncdb``).

    :return: a list
    """
    from modoboa.lib.dbutils import db_table_exists

    result = [("admin", "admin"), ("userprefs", "userprefs")]
    if db_table_exists("admin_extension"):
        exts = Extension.objects.filter(enabled=True)
        result += [(ext.name, ext.name) for ext in exts]
    return sorted(result, key=lambda e: e[0])

parameters.register_admin("DEFAULT_TOP_REDIRECTION", type="list", deflt="admin",
                          app="general",
                          values=enabled_applications(),
                          help=ugettext_lazy("The default redirection used when no application is specified"))

@events.observe("ExtDisabled")
def unset_default_topredirection(extension):
    """
    Simple callback to change the default redirection if the
    corresponding extension is being disabled.
    """
    topredirection = parameters.get_admin("DEFAULT_TOP_REDIRECTION", app="general")
    if topredirection == extension.name:
        parameters.save_admin("DEFAULT_TOP_REDIRECTION", "userprefs", app="general")

@events.observe("ExtDisabled", "ExtEnabled")
def update_available_applications(extension):
    """Simple callback to update the list of available applications

    Must be called each time an extension is disabled/enabled.
    """
    parameters.update_admin("DEFAULT_TOP_REDIRECTION", app="general",
                            values=enabled_applications())
