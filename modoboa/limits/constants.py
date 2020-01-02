"""Modoboa limits constants."""

import collections

from django.utils.translation import ugettext_lazy as _

DEFAULT_USER_LIMITS = collections.OrderedDict((
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
        "extra_filters": {"groups__name": "DomainAdmins"}}),
    ("quota", {
        "content_type": "admin.domain", "label": _("Quota"),
        "help": _("Quota shared between domains of this reseller"),
        "required_role": "Resellers",
        "type": "sum",
        "field": "quota"
    })
))


DEFAULT_DOMAIN_LIMITS = collections.OrderedDict((
    ("domain_aliases", {
        "relation": "domainalias_set", "label": _("Domain aliases"),
        "help": _("Maximum number of domain aliases allowed for this domain.")
    }),
    ("mailboxes", {
        "relation": "mailbox_set", "label": _("Mailboxes"),
        "help": _("Maximum number of mailboxes allowed for this domain.")}),
    ("mailbox_aliases", {
        "relation": "alias_set", "label": _("Mailbox aliases"),
        "help": _(
            "Maximum number of mailbox aliases allowed for this domain."),
        "extra_filters": {"internal": False}
    }),
    ("domain_admins", {
        "relation": "admins", "label": _("Domain admins"),
        "help": _("Maximum number of domain admins allowed for this domain."),
    })
))
