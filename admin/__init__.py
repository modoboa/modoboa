# -*- coding: utf-8 -*-

from modoboa.lib import parameters, events
from django.utils.translation import ugettext as _
from models import Extension

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

parameters.register_admin("DEFAULT_TOP_REDIRECTION", type="list", deflt="admin",
                          app="general",
                          values=sorted([("admin", "admin"), ("userprefs", "userprefs")] \
                                            + map(lambda ext: (ext.name, ext.name), 
                                                  Extension.objects.filter(enabled=True))),
                          help=_("The default redirection used when no application is specified"))

def unset_default_topredirection(**kwargs):
    """
    Simple callback to change the default redirection if the
    corresponding extension is being disabled.
    """
    topredirection = parameters.get_admin("DEFAULT_TOP_REDIRECTION", app="general")
    if topredirection == kwargs["ext"].name:
        parameters.save_admin("DEFAULT_TOP_REDIRECTION", "userprefs", app="general")

events.register("ExtDisabled", unset_default_topredirection)
