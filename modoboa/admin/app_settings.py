"""Modoboa admin settings."""

import collections
import os

from django import forms
from django.conf import settings
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _, ugettext_lazy
from django.forms.fields import GenericIPAddressField

from modoboa.lib.form_utils import SeparatorField, YesNoField
from modoboa.lib.sysutils import exec_cmd
from modoboa.parameters import forms as param_forms

from . import constants


class AdminParametersForm(param_forms.AdminParametersForm):
    app = "admin"

    dom_sep = SeparatorField(label=ugettext_lazy("Domains"))

    enable_mx_checks = YesNoField(
        label=ugettext_lazy("Enable MX checks"),
        initial=True,
        help_text=ugettext_lazy(
            "Check that every domain has a valid MX record"
        )
    )

    valid_mxs = forms.CharField(
        label=ugettext_lazy("Valid MXs"),
        initial="",
        help_text=ugettext_lazy(
            "A list of IP or network address every MX record should match."
            " A warning will be sent if a record does not respect it."
        ),
        widget=forms.Textarea,
        required=False
    )

    domains_must_have_authorized_mx = YesNoField(
        label=ugettext_lazy("New domains must use authorized MX(s)"),
        initial=False,
        help_text=ugettext_lazy(
            "Prevent the creation of a new domain if its MX record does "
            "not use one of the defined addresses."
        )
    )

    enable_spf_checks = YesNoField(
        label=ugettext_lazy("Enable SPF checks"),
        initial=True,
        help_text=ugettext_lazy(
            "Check if every domain has a valid SPF record"
        )
    )

    enable_dkim_checks = YesNoField(
        label=ugettext_lazy("Enable DKIM checks"),
        initial=True,
        help_text=ugettext_lazy(
            "Check if every domain with DKIM signin enabled has a valid DNS "
            "record"
        )
    )

    enable_dmarc_checks = YesNoField(
        label=ugettext_lazy("Enable DMARC checks"),
        initial=True,
        help_text=ugettext_lazy(
            "Check if every domain has a valid DMARC record"
        )
    )

    enable_autoconfig_checks = YesNoField(
        label=ugettext_lazy("Enable autoconfig checks"),
        initial=True,
        help_text=ugettext_lazy(
            "Check if every domain has a valid records for autoconfiguration"
        )
    )

    enable_dnsbl_checks = YesNoField(
        label=ugettext_lazy("Enable DNSBL checks"),
        initial=True,
        help_text=ugettext_lazy(
            "Check every domain against major DNSBL providers"
        )
    )

    custom_dns_server = GenericIPAddressField(
        label=ugettext_lazy("Custom DNS server"),
        required=False,
        help_text=ugettext_lazy(
            "Use a custom DNS server instead of local server configuration"
        )
    )

    dkim_keys_storage_dir = forms.CharField(
        label=ugettext_lazy("DKIM keys storage directory"),
        initial="",
        help_text=ugettext_lazy(
            "Absolute path of the directory where DKIM private keys will "
            "be stored. Make sure this directory belongs to root user "
            "and is not readable by the outside world."
        ),
        required=False
    )

    dkim_default_key_length = forms.ChoiceField(
        label=ugettext_lazy("Default DKIM key length"),
        initial=2048,
        choices=constants.DKIM_KEY_LENGTHS,
        help_text=ugettext_lazy(
            "Default length in bits for newly generated DKIM keys."
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

    default_domain_message_limit = forms.IntegerField(
        label=ugettext_lazy("Default domain sending limit"),
        required=False,
        help_text=ugettext_lazy(
            "Number of messages freshly created domains will be "
            "allowed to send per day. Leave empty for no limit."
        )
    )

    mbsep = SeparatorField(label=ugettext_lazy("Mailboxes"))

    handle_mailboxes = YesNoField(
        label=ugettext_lazy("Handle mailboxes on filesystem"),
        initial=False,
        help_text=ugettext_lazy(
            "Rename or remove mailboxes on the filesystem when they get"
            " renamed or removed within Modoboa"
        )
    )

    default_mailbox_quota = forms.IntegerField(
        label=ugettext_lazy("Default mailbox quota"),
        initial=0,
        help_text=ugettext_lazy(
            "Default mailbox quota (in MB) applied to freshly created "
            "mailboxes with no value specified. A value of 0 means no quota."
        )
    )

    default_mailbox_message_limit = forms.IntegerField(
        label=ugettext_lazy("Default mailbox sending limit"),
        required=False,
        help_text=ugettext_lazy(
            "Number of messages freshly created mailboxes will be "
            "allowed to send per day. Leave empty for no limit."
        )
    )

    auto_account_removal = YesNoField(
        label=ugettext_lazy("Automatic account removal"),
        initial=False,
        help_text=ugettext_lazy(
            "When a mailbox is removed, also remove the associated account")
    )

    auto_create_domain_and_mailbox = YesNoField(
        label=ugettext_lazy("Automatic domain/mailbox creation"),
        initial=True,
        help_text=ugettext_lazy(
            "Create a domain and a mailbox when an account is automatically "
            "created."
        )
    )

    create_alias_on_mbox_rename = YesNoField(
        label=ugettext_lazy("Create an alias when a mailbox is renamed"),
        initial=False,
        help_text=ugettext_lazy(
            "Create an alias using the old address when a mailbox is renamed."
        )
    )

    # Visibility rules
    visibility_rules = {
        "valid_mxs": "enable_mx_checks=True",
        "domains_must_have_authorized_mx": "enable_mx_checks=True"
    }

    def __init__(self, *args, **kwargs):
        super(AdminParametersForm, self).__init__(*args, **kwargs)
        self.field_widths = {
            "default_domain_quota": 2,
            "default_mailbox_quota": 2
        }
        hide_fields = False
        dpath = None
        code, output = exec_cmd("which dovecot")
        if not code:
            dpath = force_text(output).strip()
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
                version = force_text(version)
                if code or not version.strip().startswith("2"):
                    hide_fields = True
        else:
            hide_fields = True
        if hide_fields:
            del self.fields["handle_mailboxes"]

    def clean_default_domain_quota(self):
        """Ensure quota is a positive integer."""
        if self.cleaned_data["default_domain_quota"] < 0:
            raise forms.ValidationError(
                ugettext_lazy("Must be a positive integer")
            )
        return self.cleaned_data["default_domain_quota"]

    def clean_default_mailbox_quota(self):
        """Ensure quota is a positive integer."""
        if self.cleaned_data["default_mailbox_quota"] < 0:
            raise forms.ValidationError(
                ugettext_lazy("Must be a positive integer")
            )
        return self.cleaned_data["default_mailbox_quota"]

    def clean_dkim_keys_storage_dir(self):
        """Check that directory exists."""
        storage_dir = self.cleaned_data.get("dkim_keys_storage_dir", "")
        if storage_dir:
            if not os.path.isdir(storage_dir):
                raise forms.ValidationError(
                    ugettext_lazy("Directory not found.")
                )
            code, output = exec_cmd("which openssl")
            if code:
                raise forms.ValidationError(
                    ugettext_lazy(
                        "openssl not found, please make sure it is installed.")
                )
        return storage_dir

    def clean(self):
        """Check MX options."""
        cleaned_data = super(AdminParametersForm, self).clean()
        condition = (
            cleaned_data.get("enable_mx_checks") and
            cleaned_data.get("domains_must_have_authorized_mx") and
            not cleaned_data.get("valid_mxs"))
        if condition:
            self.add_error(
                "valid_mxs",
                _("Define at least one authorized network / address")
            )
        return cleaned_data


GLOBAL_PARAMETERS_STRUCT = collections.OrderedDict([
    ("domains", {
        "label": ugettext_lazy("Domains"),
        "params": collections.OrderedDict([
            ("enable_mx_checks", {
                "label": ugettext_lazy("Enable MX checks"),
                "help_text": ugettext_lazy(
                    "Check that every domain has a valid MX record"
                )
            }),
            ("valid_mxs", {
                "label": ugettext_lazy("Valid MXs"),
                "display": "enable_mx_checks=true",
                "help_text": ugettext_lazy(
                    "A list of IP or network address every MX record should "
                    "match. A warning will be sent if a record does not "
                    "respect it."
                ),
            }),
            ("domains_must_have_authorized_mx", {
                "label": ugettext_lazy("New domains must use authorized MX(s)"),
                "display": "enable_mx_checks=true",
                "help_text": ugettext_lazy(
                    "Prevent the creation of a new domain if its MX record "
                    "does not use one of the defined addresses."
                )
            }),
            ("enable_spf_checks", {
                "label": ugettext_lazy("Enable SPF checks"),
                "help_text": ugettext_lazy(
                    "Check if every domain has a valid SPF record"
                )
            }),
            ("enable_dkim_checks", {
                "label": ugettext_lazy("Enable DKIM checks"),
                "help_text": ugettext_lazy(
                    "Check if every domain with DKIM signin enabled "
                    "has a valid DNS record"
                )
            }),
            ("enable_dmarc_checks", {
                "label": ugettext_lazy("Enable DMARC checks"),
                "help_text": ugettext_lazy(
                    "Check if every domain has a valid DMARC record"
                )
            }),
            ("enable_autoconfig_checks", {
                "label": ugettext_lazy("Enable SPF checks"),
                "help_text": ugettext_lazy(
                    "Check if every domain has a valid records for "
                    "autoconfiguration"
                )
            }),
            ("enable_dnsbl_checks", {
                "label": ugettext_lazy("Enable DNSBL checks"),
                "help_text": ugettext_lazy(
                    "Check every domain against major DNSBL providers"
                )
            }),
            ("custom_dns_server", {
                "label": ugettext_lazy("Custom DNS server"),
                "help_text": ugettext_lazy(
                    "Use a custom DNS server instead of local server "
                    "configuration"
                )
            }),
            ("dkim_keys_storage_dir", {
                "label": ugettext_lazy("DKIM keys storage directory"),
                "help_text": ugettext_lazy(
                    "Absolute path of the directory where DKIM private keys "
                    "will be stored. Make sure this directory belongs to root "
                    "user and is not readable by the outside world."
                ),
            }),
            ("dkim_default_key_length", {
                "label": ugettext_lazy("Default DKIM key length"),
                "help_text": ugettext_lazy(
                    "Default length in bits for newly generated DKIM keys."
                )
            }),
            ("default_domain_quota", {
                "label": ugettext_lazy("Default domain quota"),
                "help_text": ugettext_lazy(
                    "Default quota (in MB) applied to freshly created domains "
                    "with no value specified. A value of 0 means no quota."
                )
            }),
            ("default_domain_message_limit", {
                "label": ugettext_lazy("Default domain sending limit"),
                "help_text": ugettext_lazy(
                    "Number of messages freshly created domains will be "
                    "allowed to send per day. Leave empty for no limit."
                )
            }),
        ])
    }),
    ("mailboxes", {
        "label": ugettext_lazy("Mailboxes"),
        "params": collections.OrderedDict([
            ("handle_mailboxes", {
                "label": ugettext_lazy("Handle mailboxes on filesystem"),
                "help_text": ugettext_lazy(
                    "Rename or remove mailboxes on the filesystem when they get"
                    " renamed or removed within Modoboa"
                )
            }),
            ("default_mailbox_quota", {
                "label": ugettext_lazy("Default mailbox quota"),
                "help_text": ugettext_lazy(
                    "Default mailbox quota (in MB) applied to freshly created "
                    "domains with no value specified. A value of 0 means no "
                    "quota."
                )
            }),
            ("default_mailbox_message_limit", {
                "label": ugettext_lazy("Default mailbox sending limit"),
                "help_text": ugettext_lazy(
                    "Number of messages freshly created mailboxes will be "
                    "allowed to send per day. Leave empty for no limit."
                )
            }),
            ("auto_account_removal", {
                "label": ugettext_lazy("Automatic account removal"),
                "help_text": ugettext_lazy(
                    "When a mailbox is removed, also remove the associated "
                    "account")
            }),
            ("auto_create_domain_and_mailbox", {
                "label": ugettext_lazy("Automatic domain/mailbox creation"),
                "help_text": ugettext_lazy(
                    "Create a domain and a mailbox when an account is "
                    "automatically created."
                )
            }),
            ("create_alias_on_mbox_rename", {
                "label": ugettext_lazy(
                    "Create an alias when a mailbox is renamed"),
                "help_text": ugettext_lazy(
                    "Create an alias using the old address when a mailbox is "
                    "renamed."
                )
            })
        ])
    }),
])


def load_admin_settings():
    """Load admin settings."""
    from modoboa.parameters import tools as param_tools
    from .api.v2 import serializers

    param_tools.registry.add(
        "global", AdminParametersForm, ugettext_lazy("Administration"))
    param_tools.registry.add2(
        "global", "admin", ugettext_lazy("Administration"),
        GLOBAL_PARAMETERS_STRUCT,
        serializers.AdminGlobalParametersSerializer)
