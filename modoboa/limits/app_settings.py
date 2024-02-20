"""Custom settings."""

import collections

from django import forms
from django.utils.translation import gettext_lazy as _

from modoboa.lib.form_utils import SeparatorField, YesNoField
from modoboa.parameters import forms as param_forms


class ParametersForm(param_forms.AdminParametersForm):
    """Available admin parameters."""

    app = "limits"

    defv_sep = SeparatorField(label=_("Default per-admin limits"))

    enable_admin_limits = YesNoField(
        label=_("Enable per-admin limits"),
        initial=True,
        help_text=_("Enable or disable per-admin limits"),
    )

    deflt_user_domain_admins_limit = forms.IntegerField(
        label=_("Domain admins"),
        initial=0,
        help_text=_(
            "Maximum number of allowed domain administrators for a new "
            "administrator. (0 to deny any creation, -1 to allow unlimited "
            "creations)"
        ),
        widget=forms.widgets.TextInput(attrs={"class": "col-md-1 form-control"}),
    )
    deflt_user_domains_limit = forms.IntegerField(
        label=_("Domains"),
        initial=0,
        help_text=_(
            "Maximum number of allowed domains for a new administrator. "
            "(0 to deny any creation, -1 to allow unlimited creations)"
        ),
        widget=forms.widgets.TextInput(attrs={"class": "col-md-1 form-control"}),
    )
    deflt_user_domain_aliases_limit = forms.IntegerField(
        label=_("Domain aliases"),
        initial=0,
        help_text=_(
            "Maximum number of allowed domain aliases for a new "
            "administrator. (0 to deny any creation, -1 to allow "
            "unlimited creations)"
        ),
        widget=forms.widgets.TextInput(attrs={"class": "col-md-1 form-control"}),
    )
    deflt_user_mailboxes_limit = forms.IntegerField(
        label=_("Mailboxes"),
        initial=0,
        help_text=_(
            "Maximum number of allowed mailboxes for a new administrator. "
            "(0 to deny any creation, -1 to allow unlimited creations)"
        ),
        widget=forms.widgets.TextInput(attrs={"class": "col-md-1 form-control"}),
    )
    deflt_user_mailbox_aliases_limit = forms.IntegerField(
        label=_("Mailbox aliases"),
        initial=0,
        help_text=_(
            "Maximum number of allowed aliases for a new administrator. "
            "(0 to deny any creation, -1 to allow unlimited creations)"
        ),
        widget=forms.widgets.TextInput(attrs={"class": "col-md-1 form-control"}),
    )
    deflt_user_quota_limit = forms.IntegerField(
        label=_("Quota"),
        initial=0,
        help_text=_(
            "The quota a reseller will be allowed to share between the "
            "domains he creates. (0 means no quota)"
        ),
        widget=forms.widgets.TextInput(attrs={"class": "col-md-1 form-control"}),
    )

    domain_limits_sep = SeparatorField(label=_("Default per-domain limits"))

    enable_domain_limits = YesNoField(
        label=_("Enable per-domain limits"),
        initial=False,
        help_text=_("Enable or disable per-domain limits"),
    )

    deflt_domain_domain_admins_limit = forms.IntegerField(
        label=_("Domain admins"),
        initial=0,
        help_text=_(
            "Maximum number of allowed domain administrators for a new "
            "domain. (0 to deny any creation, -1 to allow unlimited "
            "creations)"
        ),
        widget=forms.widgets.TextInput(attrs={"class": "col-md-1 form-control"}),
    )
    deflt_domain_domain_aliases_limit = forms.IntegerField(
        label=_("Domain aliases"),
        initial=0,
        help_text=_(
            "Maximum number of allowed domain aliases for a new "
            "domain. (0 to deny any creation, -1 to allow "
            "unlimited creations)"
        ),
        widget=forms.widgets.TextInput(attrs={"class": "col-md-1 form-control"}),
    )
    deflt_domain_mailboxes_limit = forms.IntegerField(
        label=_("Mailboxes"),
        initial=0,
        help_text=_(
            "Maximum number of allowed mailboxes for a new domain. "
            "(0 to deny any creation, -1 to allow unlimited creations)"
        ),
        widget=forms.widgets.TextInput(attrs={"class": "col-md-1 form-control"}),
    )
    deflt_domain_mailbox_aliases_limit = forms.IntegerField(
        label=_("Mailbox aliases"),
        initial=0,
        help_text=_(
            "Maximum number of allowed aliases for a new domain. "
            "(0 to deny any creation, -1 to allow unlimited creations)"
        ),
        widget=forms.widgets.TextInput(attrs={"class": "col-md-1 form-control"}),
    )

    visibility_rules = {
        "deflt_user_domains_limit": "enable_admin_limits=True",
        "deflt_user_domain_aliases_limit": "enable_admin_limits=True",
        "deflt_user_mailboxes_limit": "enable_admin_limits=True",
        "deflt_user_mailbox_aliases_limit": "enable_admin_limits=True",
        "deflt_user_domain_admins_limit": "enable_admin_limits=True",
        "deflt_domain_mailboxes_limit": "enable_domain_limits=True",
        "deflt_domain_mailbox_aliases_limit": "enable_domain_limits=True",
        "deflt_domain_domain_aliases_limit": "enable_domain_limits=True",
        "deflt_domain_domain_admins_limit": "enable_domain_limits=True",
    }


GLOBAL_PARAMETERS_STRUCT = collections.OrderedDict(
    [
        (
            "per_admin_limits",
            {
                "label": _("Default per-admin limits"),
                "params": collections.OrderedDict(
                    [
                        (
                            "enable_admin_limits",
                            {
                                "label": _("Enable per-admin limits"),
                                "help_text": _("Enable or disable per-admin limits"),
                            },
                        ),
                        (
                            "deflt_user_domain_admins_limit",
                            {
                                "label": _("Domain admins"),
                                "display": "enable_admin_limits=true",
                                "help_text": _(
                                    "Maximum number of allowed domain administrators for a new "
                                    "administrator. (0 to deny any creation, -1 to allow "
                                    "unlimited creations)"
                                ),
                            },
                        ),
                        (
                            "deflt_user_domains_limit",
                            {
                                "label": _("Domains"),
                                "display": "enable_admin_limits=true",
                                "help_text": _(
                                    "Maximum number of allowed domains for a new administrator."
                                    " (0 to deny any creation, -1 to allow unlimited creations)"
                                ),
                            },
                        ),
                        (
                            "deflt_user_domain_aliases_limit",
                            {
                                "label": _("Domain aliases"),
                                "display": "enable_admin_limits=true",
                                "help_text": _(
                                    "Maximum number of allowed domain aliases for a new "
                                    "administrator. (0 to deny any creation, -1 to allow "
                                    "unlimited creations)"
                                ),
                            },
                        ),
                        (
                            "deflt_user_mailboxes_limit",
                            {
                                "label": _("Mailboxes"),
                                "display": "enable_admin_limits=true",
                                "help_text": _(
                                    "Maximum number of allowed mailboxes for a new "
                                    "administrator. (0 to deny any creation, -1 to allow "
                                    "unlimited creations)"
                                ),
                            },
                        ),
                        (
                            "deflt_user_mailbox_aliases_limit",
                            {
                                "label": _("Mailbox aliases"),
                                "display": "enable_admin_limits=true",
                                "help_text": _(
                                    "Maximum number of allowed aliases for a new administrator."
                                    " (0 to deny any creation, -1 to allow unlimited creations)"
                                ),
                            },
                        ),
                        (
                            "deflt_user_quota_limit",
                            {
                                "label": _("Quota"),
                                "help_text": _(
                                    "The quota a reseller will be allowed to share between the "
                                    "domains he creates. (0 means no quota)"
                                ),
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "per_domain_limits",
            {
                "label": _("Default per-domain limits"),
                "params": collections.OrderedDict(
                    [
                        (
                            "enable_domain_limits",
                            {
                                "label": _("Enable per-domain limits"),
                                "help_text": _("Enable or disable per-domain limits"),
                            },
                        ),
                        (
                            "deflt_domain_domain_admins_limit",
                            {
                                "label": _("Domain admins"),
                                "display": "enable_domain_limits=true",
                                "help_text": _(
                                    "Maximum number of allowed domain administrators for a new "
                                    "domain. (0 to deny any creation, -1 to allow unlimited "
                                    "creations)"
                                ),
                            },
                        ),
                        (
                            "deflt_domain_domain_aliases_limit",
                            {
                                "label": _("Domain aliases"),
                                "display": "enable_domain_limits=true",
                                "help_text": _(
                                    "Maximum number of allowed domain aliases for a new "
                                    "domain. (0 to deny any creation, -1 to allow "
                                    "unlimited creations)"
                                ),
                            },
                        ),
                        (
                            "deflt_domain_mailboxes_limit",
                            {
                                "label": _("Mailboxes"),
                                "display": "enable_domain_limits=true",
                                "help_text": _(
                                    "Maximum number of allowed mailboxes for a new domain. "
                                    "(0 to deny any creation, -1 to allow unlimited creations)"
                                ),
                            },
                        ),
                        (
                            "deflt_domain_mailbox_aliases_limit",
                            {
                                "label": _("Mailbox aliases"),
                                "display": "enable_domain_limits=true",
                                "help_text": _(
                                    "Maximum number of allowed aliases for a new domain. "
                                    "(0 to deny any creation, -1 to allow unlimited creations)"
                                ),
                            },
                        ),
                    ]
                ),
            },
        ),
    ]
)
