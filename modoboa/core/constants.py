"""Core application constants."""

from django.conf import settings
from django.utils.translation import gettext_lazy

SIMPLEUSERS_ROLE = ("SimpleUsers", gettext_lazy("Simple user"))
DOMAINADMINS_ROLE = ("DomainAdmins", gettext_lazy("Domain administrator"))
RESELLERS_ROLE = ("Resellers", gettext_lazy("Reseller"))
SUPERADMINS_ROLE = ("SuperAdmins", gettext_lazy("Super administrator"))

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
    ("br", "breton"),
    ("cs", "čeština"),
    ("de", "deutsch"),
    ("en", "english"),
    ("el", "ελληνικά"),
    ("es", "español"),
    ("fi", "Suomalainen"),
    ("fr", "français"),
    ("it", "italiano"),
    ("ja", "日本の"),
    ("nl", "nederlands"),
    ("pt", "português"),
    ("pt-br", "português (BR)"),
    ("pl", "polski"),
    ("ro", "Română"),
    ("ru", "русский"),
    ("sv", "svenska"),
    ("tr", "türk"),
    ("zh-hant", "中文（台灣）"),
)


LDAP_GROUP_TYPES = (
    ("posixgroup", "PosixGroup"),
    ("groupofnames", "GroupOfNames"),
)

LDAP_SECURE_MODES = [
    ("none", gettext_lazy("No")),
    ("starttls", "STARTTLS"),
    ("ssl", "SSL/TLS"),
]

LDAP_AUTH_METHODS = [
    ("searchbind", gettext_lazy("Search and bind")),
    ("directbind", gettext_lazy("Direct bind")),
]

PERMISSIONS = {
    "SimpleUsers": [],
    "DomainAdmins": [
        ["core", "user", "add_user"],
        ["core", "user", "change_user"],
        ["core", "user", "delete_user"],
        ["admin", "domain", "view_domain"],
        ["admin", "mailbox", "add_mailbox"],
        ["admin", "mailbox", "change_mailbox"],
        ["admin", "mailbox", "delete_mailbox"],
        ["admin", "mailbox", "view_mailbox"],
        ["admin", "alias", "add_alias"],
        ["admin", "alias", "change_alias"],
        ["admin", "alias", "delete_alias"],
        ["admin", "alias", "view_alias"],
        ["admin", "senderaddress", "add_senderaddress"],
        ["admin", "senderaddress", "change_senderaddress"],
        ["admin", "senderaddress", "delete_senderaddress"],
        ["admin", "domainalias", "view_domainalias"],
    ],
    "Resellers": [
        ["core", "user", "add_user"],
        ["core", "user", "change_user"],
        ["core", "user", "delete_user"],
        ["admin", "mailbox", "add_mailbox"],
        ["admin", "mailbox", "change_mailbox"],
        ["admin", "mailbox", "delete_mailbox"],
        ["admin", "mailbox", "view_mailbox"],
        ["admin", "alias", "add_alias"],
        ["admin", "alias", "change_alias"],
        ["admin", "alias", "delete_alias"],
        ["admin", "alias", "view_alias"],
        ["admin", "senderaddress", "add_senderaddress"],
        ["admin", "senderaddress", "change_senderaddress"],
        ["admin", "senderaddress", "delete_senderaddress"],
        ["admin", "domain", "add_domain"],
        ["admin", "domain", "change_domain"],
        ["admin", "domain", "delete_domain"],
        ["admin", "domain", "view_domain"],
        ["admin", "domainalias", "add_domainalias"],
        ["admin", "domainalias", "change_domainalias"],
        ["admin", "domainalias", "delete_domainalias"],
    ],
}

SMS_BACKENDS = [
    ("", gettext_lazy("Choose a provider")),
    ("ovh", "OVH"),
]

if settings.DEBUG:
    SMS_BACKENDS.insert(1, ("dummy", gettext_lazy("Dummy")))

TFA_DEVICE_TOKEN_KEY = "otp_device_id"
TFA_PRE_VERIFY_USER_PK = "tfa_pre_verify_user_pk"
TFA_PRE_VERIFY_USER_BACKEND = "tfa_pre_verify_user_backend"

DOVEADM_PASS_SCHEME_ALARM = "doveadm_password_scheme_fail"
