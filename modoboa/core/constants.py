# -*- coding: utf-8 -*-

"""Core application constants."""

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy

SIMPLEUSERS_ROLE = ("SimpleUsers", ugettext_lazy("Simple user"))
DOMAINADMINS_ROLE = ("DomainAdmins", ugettext_lazy("Domain administrator"))
RESELLERS_ROLE = ("Resellers", ugettext_lazy("Reseller"))
SUPERADMINS_ROLE = ("SuperAdmins", ugettext_lazy("Super administrator"))

ROLES = (
    SIMPLEUSERS_ROLE,
    DOMAINADMINS_ROLE,
    RESELLERS_ROLE,
    SUPERADMINS_ROLE,
)

ADMIN_GROUPS = [
    "SuperAdmins",
    "Resellers",
    "DomainAdmins",
]

LANGUAGES = (
    ("br", u"breton"),
    ("cs", u"čeština"),
    ("de", u"deutsch"),
    ("en", u"english"),
    ("el_GR", u"ελληνικά"),
    ("es", u"español"),
    ("fr", u"français"),
    ("it", u"italiano"),
    ("ja_JP", u"日本の"),
    ("nl", u"nederlands"),
    ("pt_PT", u"português"),
    ("pt_BR", u"português (BR)"),
    ("pl_PL", u"polski"),
    ("ro_RO", u"Română"),
    ("ru", u"русский"),
    ("sv", u"svenska"),
    ("tr_TR", u"türk"),
    ("zh_TW", u"中文（台灣）"),
)


LDAP_GROUP_TYPES = (
    ("posixgroup", "PosixGroup"),
    ("groupofnames", "GroupOfNames"),
)

LDAP_SECURE_MODES = [
    ("none", ugettext_lazy("No")),
    ("starttls", "STARTTLS"),
    ("ssl", "SSL/TLS")
]

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
        ["admin", "mailbox", "view_mailboxes"],
        ["admin", "alias", "add_alias"],
        ["admin", "alias", "change_alias"],
        ["admin", "alias", "delete_alias"],
        ["admin", "alias", "view_aliases"],
        ["admin", "senderaddress", "add_senderaddress"],
        ["admin", "senderaddress", "change_senderaddress"],
        ["admin", "senderaddress", "delete_senderaddress"],
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
        ["admin", "mailbox", "view_mailboxes"],
        ["admin", "alias", "add_alias"],
        ["admin", "alias", "change_alias"],
        ["admin", "alias", "delete_alias"],
        ["admin", "alias", "view_aliases"],
        ["admin", "senderaddress", "add_senderaddress"],
        ["admin", "senderaddress", "change_senderaddress"],
        ["admin", "senderaddress", "delete_senderaddress"],
        ["admin", "domain", "view_domains"],
        ["admin", "domain", "add_domain"],
        ["admin", "domain", "change_domain"],
        ["admin", "domain", "delete_domain"],
        ["admin", "domainalias", "add_domainalias"],
        ["admin", "domainalias", "change_domainalias"],
        ["admin", "domainalias", "delete_domainalias"],
    ]
}
