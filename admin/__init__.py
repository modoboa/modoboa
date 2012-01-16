# -*- coding: utf-8 -*-

from modoboa.lib import parameters, events
from django.utils.translation import ugettext as _
from django.db.utils import DatabaseError
from models import Extension

parameters.register_admin("AUTHENTICATION_TYPE", type="list", deflt="local",
                          values=[('local', _("Local")),
                                  ('ldap', "LDAP")],
                          help=_("The backend used for authentication"))
parameters.register_admin("CREATE_DIRECTORIES", type="list_yesno", deflt="yes",
			  help=_("Modoboa will handle mailbox creation on filesystem"))
parameters.register_admin("STORAGE_PATH", type="string", deflt="/var/vmail",
                          help=_("Path to the root directory where messages are stored"))
parameters.register_admin("VIRTUAL_UID", type="string", deflt="vmail",
                          help=_("UID of the virtual user which owns domains/mailboxes/messages on the filesystem"))
parameters.register_admin("VIRTUAL_GID", type="string", deflt="vmail",
                          help=_("GID of the virtual user which owns domains/mailboxes/messages on the filesystem"))
parameters.register_admin("MAILBOX_TYPE", type="list", deflt="maildir",
                          values=[("maildir", "maildir"), ("mbox", "mbox")],
                          help=_("Mailboxes storage format"))
parameters.register_admin("MAILDIR_ROOT", type="string", deflt=".maildir",
                          help=_("Sub-directory (inside the mailbox) where messages are stored when using the maildir format"))
parameters.register_admin("PASSWORD_SCHEME", type="list", deflt="crypt",
                          values=[("crypt", "crypt"), ("md5", "md5"), ("clear", "clear")],
                          help=_("Scheme used to crypt mailbox passwords"))
parameters.register_admin("ITEMS_PER_PAGE", type="int", deflt=30,
                          help=_("Number of displayed items per page"))

def enabled_applications():
    """Return the list of currently enabled extensions

    Quick fix for #184:

    Just catch the DatabaseError exception raised when runnning the
    first ``syncdb`` command.

    :return: a list
    """
    result = [("admin", "admin"), ("userprefs", "userprefs")]
    try:
        exts = list(Extension.objects.filter(enabled=True))
    except DatabaseError:
        exts = []
    result += map(lambda ext: (ext.name, ext.name), exts)
    return sorted(result)

parameters.register_admin("DEFAULT_TOP_REDIRECTION", type="list", deflt="admin",
                          app="general",
                          values=enabled_applications(),
                          help=_("The default redirection used when no application is specified"))

def unset_default_topredirection(**kwargs):
    """
    Simple callback to change the default redirection if the
    corresponding extension is being disabled.
    """
    topredirection = parameters.get_admin("DEFAULT_TOP_REDIRECTION", app="general")
    if topredirection == kwargs["ext"].name:
        parameters.save_admin("DEFAULT_TOP_REDIRECTION", "userprefs", app="general")

def update_available_applications(extension):
    """Simple callback to update the list of available applications

    Must be called each time an extension is disabled/enabled.
    """
    parameters.update_admin("DEFAULT_TOP_REDIRECTION", app="general",
                            values=enabled_applications())

events.register("ExtDisabled", unset_default_topredirection)
events.register("ExtDisabled", update_available_applications)
events.register("ExtEnabled", update_available_applications)
