# -*- coding: utf-8 -*-

from mailng.lib import parameters
from django.utils.translation import ugettext as _

parameters.register("admin","STORAGE_PATH", "string", "/var/vmail",
                    help=_("Path to the root directory where messages are stored"))
parameters.register("admin", "VIRTUAL_UID", "string", "vmail",
                    help=_("UID of the virtual user which owns domains/mailboxes/messages on the filesystem"))
parameters.register("admin", "VIRTUAL_GID", "string", "vmail",
                    help=_("GID of the virtual user which owns domains/mailboxes/messages on the filesystem"))
parameters.register("admin", "MAILBOX_TYPE", "list", "maildir",
                    values=[("maildir", "maildir"), ("mbox", "mbox")],
                    help=_("Mailboxes storage format"))
parameters.register("admin", "MAILDIR_ROOT", "string", ".maildir",
                    help=_("Sub-directory (inside the mailbox) where messages are stored when using the maildir format"))
parameters.register("admin", "PASSWORD_SCHEME", "list", "crypt",
                    values=[("crypt", "crypt"), ("md5", "md5"), ("clear", "clear")],
                    help=_("Scheme used to crypt mailbox passwords"))
