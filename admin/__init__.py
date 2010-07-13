# -*- coding: utf-8 -*-

from modoboa.lib import parameters
from django.utils.translation import ugettext as _

parameters.register_admin("admin","STORAGE_PATH", type="string", deflt="/var/vmail",
                          help=_("Path to the root directory where messages are stored"))
parameters.register_admin("admin", "VIRTUAL_UID", type="string", deflt="vmail",
                          help=_("UID of the virtual user which owns domains/mailboxes/messages on the filesystem"))
parameters.register_admin("admin", "VIRTUAL_GID", type="string", deflt="vmail",
                          help=_("GID of the virtual user which owns domains/mailboxes/messages on the filesystem"))
parameters.register_admin("admin", "MAILBOX_TYPE", type="list", deflt="maildir",
                          values=[("maildir", "maildir"), ("mbox", "mbox")],
                          help=_("Mailboxes storage format"))
parameters.register_admin("admin", "MAILDIR_ROOT", type="string", deflt=".maildir",
                          help=_("Sub-directory (inside the mailbox) where messages are stored when using the maildir format"))
parameters.register_admin("admin", "PASSWORD_SCHEME", type="list", deflt="crypt",
                          values=[("crypt", "crypt"), ("md5", "md5"), ("clear", "clear")],
                          help=_("Scheme used to crypt mailbox passwords"))
