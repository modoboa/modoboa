"""Modoboa limits constants."""

import collections

from django.utils.translation import ugettext_lazy as _


DEFAULT_LIMITS = collections.OrderedDict((
    ("domains", {
        "content_type": "admin.domain", "label": _("Domains"),
        "help": _("Maximum number of domains this user can create"),
        "required_role": "Resellers"}),
    ("domain_aliases", {
        "content_type": "admin.domainalias", "label": _("Domain aliases"),
        "help": _("Maximum number of domain aliases this user can create"),
        "required_role": "Resellers"}),
    ("mailboxes", {
        "content_type": "admin.mailbox", "label": _("Mailboxes"),
        "help": _("Maximum number of mailboxes this user can create")}),
    ("mailbox_aliases", {
        "content_type": "admin.alias", "label": _("Mailbox aliases"),
        "help": _("Maximum number of mailbox aliases this user "
                  "can create")}),
    ("domain_admins", {
        "content_type": "core.user", "label": _("Domain admins"),
        "help": _("Maximum number of domain administrators this user "
                  "can create"),
        "required_role": "Resellers",
        "extra_filters": {"groups__name": "DomainAdmins"}})
))
