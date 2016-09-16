"""Modoboa admin settings and events."""

import os

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy

from ..lib import events
from modoboa.lib import parameters
from modoboa.lib.form_utils import YesNoField, SeparatorField
from modoboa.lib.sysutils import exec_cmd


ADMIN_EVENTS = [
    "DomainCreated",
    "DomainModified",
    "DomainDeleted",
    "DomainOwnershipRemoved",
    "GetTagsForDomain",
    "ExtraDomainMenuEntries",
    "ExtraDomainFilters",
    "ExtraDomainQsetFilters",
    "ExtraDomainTypes",
    "ExtraDomainWizardSteps",
    "GetDomainModifyLink",
    "CheckDomainName",

    "DomainAliasCreated",
    "DomainAliasDeleted",

    "MailboxCreated",
    "MailboxDeleted",
    "MailboxModified",

    "MailboxAliasCreated",
    "MailboxAliasDeleted",

    "ExtraDomainForm",
    "FillDomainInstances",

    "ExtraAccountForm",
    "CheckExtraAccountForm",
    "FillAccountInstances",

    "ExtraDomainImportHelp",
    "ImportObject"
]


class AdminParametersForm(parameters.AdminParametersForm):
    app = "admin"

    dom_sep = SeparatorField(label=ugettext_lazy("Domains"))

    enable_mx_checks = YesNoField(
        label=ugettext_lazy("Enable MX checks"),
        initial="yes",
        help_text=ugettext_lazy(
            "Check that every domain has a valid MX record"
        )
    )

    valid_mxs = forms.CharField(
        label=ugettext_lazy("Valid MXs"),
        initial="",
        help_text=ugettext_lazy(
            "IP(s) or network(s) "
            "of the MX that should match with domains' MX records. "
            "On per line."
        ),
        widget=forms.Textarea,
        required=False
    )

    enable_dnsbl_checks = YesNoField(
        label=ugettext_lazy("Enable DNSBL checks"),
        initial="yes",
        help_text=ugettext_lazy(
            "Check every domain against major DNSBL providers"
        )
    )

    mbsep = SeparatorField(label=ugettext_lazy("Mailboxes"))

    handle_mailboxes = YesNoField(
        label=ugettext_lazy("Handle mailboxes on filesystem"),
        initial="no",
        help_text=ugettext_lazy(
            "Rename or remove mailboxes on the filesystem when they get"
            " renamed or removed within Modoboa"
        )
    )

    mailboxes_owner = forms.CharField(
        label=ugettext_lazy("Mailboxes owner"),
        initial="vmail",
        help_text=ugettext_lazy(
            "The UNIX account who owns mailboxes on the filesystem"
        )
    )

    default_domain_quota = forms.IntegerField(
        label=ugettext_lazy("Default domain quota"),
        initial=0,
        help_text=ugettext_lazy(
            "Default quota (in MB) applied to freshly created domains with no "
            "value specified. A value of 0 means no quota."
        )
    )

    auto_account_removal = YesNoField(
        label=ugettext_lazy("Automatic account removal"),
        initial="no",
        help_text=ugettext_lazy(
            "When a mailbox is removed, also remove the associated account")
    )

    auto_create_domain_and_mailbox = YesNoField(
        label=ugettext_lazy("Automatic domain/mailbox creation"),
        initial="yes",
        help_text=ugettext_lazy(
            "Create a domain and a mailbox when an account is automatically "
            "created."
        )
    )

    # Visibility rules
    visibility_rules = {
        "valid_mxs": "enable_mx_checks=yes",
        "mailboxes_owner": "handle_mailboxes=yes",
    }

    def __init__(self, *args, **kwargs):
        super(AdminParametersForm, self).__init__(*args, **kwargs)
        self.field_widths = {
            "default_domain_quota": 2
        }
        hide_fields = False
        dpath = None
        code, output = exec_cmd("which dovecot")
        if not code:
            dpath = output.strip()
        else:
            known_paths = getattr(
                settings, "DOVECOT_LOOKUP_PATH",
                ("/usr/sbin/dovecot", "/usr/local/sbin/dovecot")
            )
            for fpath in known_paths:
                if os.path.isfile(fpath) and os.access(fpath, os.X_OK):
                    dpath = fpath
        if dpath:
            try:
                code, version = exec_cmd("%s --version" % dpath)
            except OSError:
                hide_fields = True
            else:
                if code or not version.strip().startswith("2"):
                    hide_fields = True
        else:
            hide_fields = True
        if hide_fields:
            del self.fields["handle_mailboxes"]
            del self.fields["mailboxes_owner"]

    def clean_default_domain_quota(self):
        """Ensure quota is a positive integer."""
        if self.cleaned_data['default_domain_quota'] < 0:
            raise forms.ValidationError(
                ugettext_lazy('Must be a positive integer')
            )
        return self.cleaned_data['default_domain_quota']


def load_admin_settings():
    """Load admin settings."""
    from .app_settings import AdminParametersForm

    parameters.register(
        AdminParametersForm, ugettext_lazy("Administration"))
    events.declare(ADMIN_EVENTS)
    from . import callbacks
