"""Core settings."""

import collections

from django import forms
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import password_validation
from django.utils.translation import gettext as _, gettext_lazy

from modoboa.core.password_hashers.utils import cache_available_password_hasher
from modoboa.lib import fields as lib_fields
from modoboa.lib.form_utils import HorizontalRadioSelect, SeparatorField, YesNoField
from modoboa.parameters import forms as param_forms, tools as param_tools

from . import constants
from . import sms_backends


def enabled_applications():
    """Return the list of installed extensions."""
    from modoboa.core.extensions import exts_pool

    result = [("user", _("User profile"))]
    for extension in exts_pool.list_all():
        if "topredirection_url" not in extension:
            continue
        result.append((extension["name"], extension["label"]))
    return sorted(result, key=lambda e: e[0])


def get_password_scheme():
    available_schemes = cache.get("password_scheme_choice")
    if available_schemes is None:
        available_schemes = cache_available_password_hasher()
    return available_schemes


class GeneralParametersForm(param_forms.AdminParametersForm):
    """General parameters."""

    app = "core"

    sep1 = SeparatorField(label=gettext_lazy("Authentication"))

    authentication_type = forms.ChoiceField(
        label=gettext_lazy("Authentication type"),
        choices=[("local", gettext_lazy("Local")), ("ldap", "LDAP")],
        initial="local",
        help_text=gettext_lazy("The backend used for authentication"),
        widget=HorizontalRadioSelect(),
    )

    password_scheme = forms.ChoiceField(
        label=gettext_lazy("Default password scheme"),
        choices=[],
        initial="sha512crypt",
        help_text=gettext_lazy("Scheme used to crypt mailbox passwords"),
    )

    rounds_number = forms.IntegerField(
        label=gettext_lazy("Rounds"),
        initial=70000,
        help_text=gettext_lazy(
            "Number of rounds to use (only used by sha256crypt and "
            "sha512crypt). Must be between 1000 and 999999999, inclusive."
        ),
    )

    update_scheme = YesNoField(
        label=gettext_lazy("Update password scheme at login"),
        initial=True,
        help_text=gettext_lazy(
            "Update user password at login to use the default password scheme"
        ),
    )

    default_password = forms.CharField(
        label=gettext_lazy("Default password"),
        initial="ChangeMe1!",
        help_text=gettext_lazy("Default password for automatically created accounts."),
    )

    random_password_length = forms.IntegerField(
        label=gettext_lazy("Random password length"),
        min_value=8,
        initial=8,
        help_text=gettext_lazy("Length of randomly generated passwords."),
    )

    update_password_url = forms.URLField(
        label=gettext_lazy("Update password service URL"),
        initial="",
        required=False,
        help_text=gettext_lazy(
            "The URL of an external page where users will be able"
            " to update their password. It applies only to non local"
            " users, ie. those automatically created after a successful"
            " external authentication (LDAP, SMTP)."
        ),
    )

    password_recovery_msg = forms.CharField(
        label=gettext_lazy("Password recovery announcement"),
        initial="",
        required=False,
        widget=forms.widgets.Textarea(),
        help_text=gettext_lazy(
            "A temporary message that will be displayed on the " "reset password page."
        ),
    )

    sms_password_recovery = YesNoField(
        label=gettext_lazy("Enable password recovery by SMS"),
        initial=False,
        help_text=gettext_lazy(
            "Enable password recovery by SMS for users who filled " "a phone number."
        ),
    )

    sms_provider = forms.ChoiceField(
        label=gettext_lazy("SMS provider"),
        choices=constants.SMS_BACKENDS,
        help_text=gettext_lazy("Choose a provider to send password recovery SMS"),
        required=False,
    )

    # LDAP specific settings
    ldap_sep = SeparatorField(label=gettext_lazy("LDAP settings"))

    ldap_server_address = forms.CharField(
        label=gettext_lazy("Server address"),
        initial="localhost",
        help_text=gettext_lazy("The IP address or the DNS name of the LDAP server"),
    )

    ldap_server_port = forms.IntegerField(
        label=gettext_lazy("Server port"),
        initial=389,
        help_text=gettext_lazy("The TCP port number used by the LDAP server"),
    )

    ldap_enable_secondary_server = YesNoField(
        label=gettext_lazy("Enable secondary server (fallback)"),
        initial=False,
        help_text=gettext_lazy(
            "Enable a secondary LDAP server which will be used "
            "if the primary one fails"
        ),
    )

    ldap_secondary_server_address = forms.CharField(
        label=gettext_lazy("Secondary server address"),
        initial="localhost",
        help_text=gettext_lazy(
            "The IP address or the DNS name of the seondary LDAP server"
        ),
    )

    ldap_secondary_server_port = forms.IntegerField(
        label=gettext_lazy("Secondary server port"),
        initial=389,
        help_text=gettext_lazy("The TCP port number used by the LDAP secondary server"),
    )

    ldap_secured = forms.ChoiceField(
        label=gettext_lazy("Use a secured connection"),
        choices=constants.LDAP_SECURE_MODES,
        initial="none",
        help_text=gettext_lazy(
            "Use an SSL/STARTTLS connection to access the LDAP server"
        ),
    )

    ldap_is_active_directory = YesNoField(
        label=gettext_lazy("Active Directory"),
        initial=False,
        help_text=gettext_lazy("Tell if the LDAP server is an Active Directory one"),
    )

    ldap_admin_groups = forms.CharField(
        label=gettext_lazy("Administrator groups"),
        initial="",
        help_text=gettext_lazy(
            "Members of those LDAP Posix groups will be created as domain "
            "administrators. Use ';' characters to separate groups."
        ),
        required=False,
    )

    ldap_group_type = forms.ChoiceField(
        label=gettext_lazy("Group type"),
        initial="posixgroup",
        choices=constants.LDAP_GROUP_TYPES,
        help_text=gettext_lazy("The LDAP group type to use with your directory."),
    )

    ldap_groups_search_base = forms.CharField(
        label=gettext_lazy("Groups search base"),
        initial="",
        help_text=gettext_lazy(
            "The distinguished name of the search base used to find groups"
        ),
        required=False,
    )

    ldap_password_attribute = forms.CharField(
        label=gettext_lazy("Password attribute"),
        initial="userPassword",
        help_text=gettext_lazy("The attribute used to store user passwords"),
    )

    # LDAP authentication settings
    ldap_auth_sep = SeparatorField(label=gettext_lazy("LDAP authentication settings"))

    ldap_auth_method = forms.ChoiceField(
        label=gettext_lazy("Authentication method"),
        choices=[
            ("searchbind", gettext_lazy("Search and bind")),
            ("directbind", gettext_lazy("Direct bind")),
        ],
        initial="searchbind",
        help_text=gettext_lazy("Choose the authentication method to use"),
    )

    ldap_bind_dn = forms.CharField(
        label=gettext_lazy("Bind DN"),
        initial="",
        help_text=gettext_lazy(
            "The distinguished name to use when binding to the LDAP server. "
            "Leave empty for an anonymous bind"
        ),
        required=False,
    )

    ldap_bind_password = forms.CharField(
        label=gettext_lazy("Bind password"),
        initial="",
        help_text=gettext_lazy(
            "The password to use when binding to the LDAP server " "(with 'Bind DN')"
        ),
        widget=forms.PasswordInput(render_value=True),
        required=False,
    )

    ldap_search_base = forms.CharField(
        label=gettext_lazy("Users search base"),
        initial="",
        help_text=gettext_lazy(
            "The distinguished name of the search base used to find users"
        ),
        required=False,
    )

    ldap_search_filter = forms.CharField(
        label=gettext_lazy("Search filter"),
        initial="(mail=%(user)s)",
        help_text=gettext_lazy(
            "An optional filter string (e.g. '(objectClass=person)'). "
            "In order to be valid, it must be enclosed in parentheses."
        ),
        required=False,
    )

    ldap_user_dn_template = forms.CharField(
        label=gettext_lazy("User DN template"),
        initial="",
        help_text=gettext_lazy(
            "The template used to construct a user's DN. It should contain "
            "one placeholder (ie. %(user)s)"
        ),
        required=False,
    )

    # LDAP sync. settings
    ldap_sync_sep = SeparatorField(label=gettext_lazy("LDAP synchronization settings"))

    ldap_sync_bind_dn = forms.CharField(
        label=gettext_lazy("Bind DN"),
        initial="",
        help_text=gettext_lazy(
            "The distinguished name to use when binding to the LDAP server. "
            "Leave empty for an anonymous bind"
        ),
        required=False,
    )

    ldap_sync_bind_password = forms.CharField(
        label=gettext_lazy("Bind password"),
        initial="",
        help_text=gettext_lazy(
            "The password to use when binding to the LDAP server " "(with 'Bind DN')"
        ),
        widget=forms.PasswordInput(render_value=True),
        required=False,
    )

    ldap_enable_sync = YesNoField(
        label=gettext_lazy("Enable export to LDAP"),
        initial=False,
        help_text=gettext_lazy(
            "Enable automatic synchronization between local database and "
            "LDAP directory"
        ),
    )

    ldap_sync_delete_remote_account = YesNoField(
        label=gettext_lazy("Delete remote LDAP account when local account is deleted"),
        initial=False,
        help_text=gettext_lazy(
            "Delete remote LDAP account when local account is deleted, "
            "otherwise it will be disabled."
        ),
    )

    ldap_sync_account_dn_template = forms.CharField(
        label=gettext_lazy("Account DN template"),
        initial="",
        help_text=gettext_lazy(
            "The template used to construct an account's DN. It should contain "
            "one placeholder (ie. %(user)s)"
        ),
        required=False,
    )

    ldap_enable_import = YesNoField(
        label=gettext_lazy("Enable import from LDAP"),
        initial=False,
        help_text=gettext_lazy(
            "Enable account synchronization from LDAP directory to local " "database"
        ),
    )

    ldap_import_search_base = forms.CharField(
        label=gettext_lazy("Users search base"),
        initial="",
        help_text=gettext_lazy(
            "The distinguished name of the search base used to find users"
        ),
        required=False,
    )

    ldap_import_search_filter = forms.CharField(
        label=gettext_lazy("Search filter"),
        initial="(cn=*)",
        help_text=gettext_lazy(
            "An optional filter string (e.g. '(objectClass=person)'). "
            "In order to be valid, it must be enclosed in parentheses."
        ),
        required=False,
    )

    ldap_import_username_attr = forms.CharField(
        label=gettext_lazy("Username attribute"),
        initial="cn",
        help_text=gettext_lazy(
            "The name of the LDAP attribute where the username can be found."
        ),
    )

    ldap_dovecot_sync = YesNoField(
        label=gettext_lazy("Enable Dovecot LDAP sync"),
        initial=False,
        help_text=gettext_lazy(
            "LDAP authentication settings will be applied to Dovecot " "configuration."
        ),
    )

    ldap_dovecot_conf_file = forms.CharField(
        label=gettext_lazy("Dovecot LDAP config file"),
        initial="/etc/dovecot/dovecot-modoboa.conf",
        required=False,
        help_text=gettext_lazy(
            "Location of the configuration file which contains "
            "Dovecot LDAP settings."
        ),
    )

    dash_sep = SeparatorField(label=gettext_lazy("Dashboard"))

    rss_feed_url = forms.URLField(
        label=gettext_lazy("Custom RSS feed"),
        required=False,
        help_text=gettext_lazy(
            "Display custom RSS feed to resellers and domain administrators"
        ),
    )

    hide_features_widget = YesNoField(
        label=gettext_lazy("Hide features widget"),
        initial=False,
        help_text=gettext_lazy(
            "Hide features widget for resellers and domain administrators"
        ),
    )

    notif_sep = SeparatorField(label=gettext_lazy("Notifications"))

    sender_address = lib_fields.UTF8EmailField(
        label=_("Sender address"),
        initial="noreply@yourdomain.test",
        help_text=_("Email address used to send notifications."),
    )

    api_sep = SeparatorField(label=gettext_lazy("Public API"))

    enable_api_communication = YesNoField(
        label=gettext_lazy("Enable communication"),
        initial=True,
        help_text=gettext_lazy("Enable communication with Modoboa public API"),
    )

    check_new_versions = YesNoField(
        label=gettext_lazy("Check new versions"),
        initial=True,
        help_text=gettext_lazy("Automatically checks if a newer version is available"),
    )

    send_new_versions_email = YesNoField(
        label=gettext_lazy("Send an email when new versions are found"),
        initial=False,
        help_text=gettext_lazy("Send an email to notify admins about new versions"),
    )
    new_versions_email_rcpt = lib_fields.UTF8EmailField(
        label=_("Recipient"),
        initial="postmaster@yourdomain.test",
        help_text=_("Recipient of new versions notification emails."),
    )

    send_statistics = YesNoField(
        label=gettext_lazy("Send statistics"),
        initial=True,
        help_text=gettext_lazy(
            "Send statistics to Modoboa public API " "(counters and used extensions)"
        ),
    )

    sep3 = SeparatorField(label=gettext_lazy("Miscellaneous"))

    enable_inactive_accounts = YesNoField(
        label=_("Enable inactive account tracking"),
        initial=True,
        help_text=_(
            "Allow the administrator to set a threshold (in days) "
            "beyond which an account is considered inactive "
            "if the user hasn't logged in"
        ),
    )

    inactive_account_threshold = forms.IntegerField(
        label=_("Inactive account threshold"),
        initial=30,
        help_text=_(
            "An account with a last login date greater than this threshold "
            "(in days) will be considered as inactive"
        ),
    )

    top_notifications_check_interval = forms.IntegerField(
        label=_("Top notifications check interval"),
        initial=30,
        help_text=_("Interval between two top notification checks (in seconds)"),
    )

    log_maximum_age = forms.IntegerField(
        label=gettext_lazy("Maximum log record age"),
        initial=365,
        help_text=gettext_lazy("The maximum age in days of a log record"),
    )

    items_per_page = forms.IntegerField(
        label=gettext_lazy("Items per page"),
        initial=30,
        help_text=gettext_lazy("Number of displayed items per page"),
    )

    default_top_redirection = forms.ChoiceField(
        label=gettext_lazy("Default top redirection"),
        choices=[],
        initial="user",
        help_text=gettext_lazy(
            "The default redirection used when no application is specified"
        ),
    )

    # Visibility rules
    visibility_rules = {
        "ldap_secondary_server_address": "ldap_enable_secondary_server=True",
        "ldap_secondary_server_port": "ldap_enable_secondary_server=True",
        "ldap_auth_sep": "authentication_type=ldap",
        "ldap_auth_method": "authentication_type=ldap",
        "ldap_bind_dn": "ldap_auth_method=searchbind",
        "ldap_bind_password": "ldap_auth_method=searchbind",
        "ldap_search_base": "ldap_auth_method=searchbind",
        "ldap_search_filter": "ldap_auth_method=searchbind",
        "ldap_user_dn_template": "ldap_auth_method=directbind",
        "ldap_admin_groups": "authentication_type=ldap",
        "ldap_group_type": "authentication_type=ldap",
        "ldap_groups_search_base": "authentication_type=ldap",
        "ldap_sync_delete_remote_account": "ldap_enable_sync=True",
        "ldap_sync_account_dn_template": "ldap_enable_sync=True",
        "ldap_import_search_base": "ldap_enable_import=True",
        "ldap_import_search_filter": "ldap_enable_import=True",
        "ldap_import_username_attr": "ldap_enable_import=True",
        "ldap_dovecot_conf_file": "ldap_dovecot_sync=True",
        "check_new_versions": "enable_api_communication=True",
        "send_statistics": "enable_api_communication=True",
        "send_new_versions_email": "check_new_versions=True",
        "new_versions_email_rcpt": "check_new_versions=True",
        "sms_provider": "sms_password_recovery=True",
        "inactive_account_threshold": "enable_inactive_accounts=True",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["default_top_redirection"].choices = enabled_applications()
        self._add_visibilty_rules(sms_backends.get_all_backend_visibility_rules())
        self.fields["password_scheme"].choices = get_password_scheme()

    def _add_dynamic_fields(self):
        new_fields = collections.OrderedDict()
        for field, value in self.fields.items():
            new_fields[field] = value
            if field == "sms_provider":
                sms_backend_fields = sms_backends.get_all_backend_settings()
                for field, definition in sms_backend_fields.items():
                    new_fields[field] = definition["type"](**definition["attrs"])
        self.fields = new_fields

    def clean_ldap_user_dn_template(self):
        tpl = self.cleaned_data["ldap_user_dn_template"]
        try:
            tpl % {"user": "toto"}
        except (KeyError, ValueError):
            raise forms.ValidationError(_("Invalid syntax")) from None
        return tpl

    def clean_ldap_sync_account_dn_template(self):
        tpl = self.cleaned_data["ldap_sync_account_dn_template"]
        try:
            tpl % {"user": "toto"}
        except (KeyError, ValueError):
            raise forms.ValidationError(_("Invalid syntax")) from None
        return tpl

    def clean_ldap_search_filter(self):
        ldap_filter = self.cleaned_data["ldap_search_filter"]
        try:
            ldap_filter % {"user": "toto"}
        except (KeyError, ValueError, TypeError):
            raise forms.ValidationError(_("Invalid syntax")) from None
        return ldap_filter

    def clean_rounds_number(self):
        value = self.cleaned_data["rounds_number"]
        if value < 1000 or value > 999999999:
            raise forms.ValidationError(_("Invalid rounds number"))
        return value

    def clean_default_password(self):
        """Check password complexity."""
        value = self.cleaned_data["default_password"]
        password_validation.validate_password(value)
        return value

    def clean(self):
        """Custom validation method

        Depending on 'ldap_auth_method' value, we check for different
        required parameters.
        """
        super().clean()
        cleaned_data = self.cleaned_data

        if cleaned_data["sms_password_recovery"]:
            provider = cleaned_data.get("sms_provider")
            if provider:
                sms_settings = sms_backends.get_backend_settings(provider)
                if sms_settings:
                    for name in sms_settings.keys():
                        if not cleaned_data.get(name):
                            self.add_error(name, _("This field is required"))
            else:
                self.add_error("sms_provider", _("This field is required"))
        if cleaned_data["authentication_type"] != "ldap":
            return cleaned_data

        if cleaned_data["ldap_auth_method"] == "searchbind":
            required_fields = ["ldap_search_base", "ldap_search_filter"]
        else:
            required_fields = ["ldap_user_dn_template"]

        for f in required_fields:
            if f not in cleaned_data or cleaned_data[f] == "":
                self.add_error(f, _("This field is required"))

        return cleaned_data

    def _apply_ldap_settings(self, values, backend):
        """Apply configuration for given backend."""
        import ldap
        from django_auth_ldap.config import (
            LDAPSearch,
            PosixGroupType,
            GroupOfNamesType,
            ActiveDirectoryGroupType,
        )

        if not hasattr(settings, backend.setting_fullname("USER_ATTR_MAP")):
            setattr(
                settings,
                backend.setting_fullname("USER_ATTR_MAP"),
                {"first_name": "givenName", "email": "mail", "last_name": "sn"},
            )
        ldap_uri = "ldaps://" if values["ldap_secured"] == "ssl" else "ldap://"
        ldap_uri += f"{values[backend.srv_address_setting_name]}:{values[backend.srv_port_setting_name]}"
        setattr(settings, backend.setting_fullname("SERVER_URI"), ldap_uri)
        if values["ldap_secured"] == "starttls":
            setattr(settings, backend.setting_fullname("START_TLS"), True)

        if values["ldap_is_active_directory"]:
            setattr(
                settings,
                backend.setting_fullname("GROUP_TYPE"),
                ActiveDirectoryGroupType(),
            )
            searchfilter = "(objectClass=group)"
        elif values["ldap_group_type"] == "groupofnames":
            setattr(
                settings, backend.setting_fullname("GROUP_TYPE"), GroupOfNamesType()
            )
            searchfilter = "(objectClass=groupOfNames)"
        else:
            setattr(settings, backend.setting_fullname("GROUP_TYPE"), PosixGroupType())
            searchfilter = "(objectClass=posixGroup)"
        setattr(
            settings,
            backend.setting_fullname("GROUP_SEARCH"),
            LDAPSearch(
                values["ldap_groups_search_base"], ldap.SCOPE_SUBTREE, searchfilter
            ),
        )
        if values["ldap_auth_method"] == "searchbind":
            setattr(
                settings, backend.setting_fullname("BIND_DN"), values["ldap_bind_dn"]
            )
            setattr(
                settings,
                backend.setting_fullname("BIND_PASSWORD"),
                values["ldap_bind_password"],
            )
            search = LDAPSearch(
                values["ldap_search_base"],
                ldap.SCOPE_SUBTREE,
                values["ldap_search_filter"],
            )
            setattr(settings, backend.setting_fullname("USER_SEARCH"), search)
        else:
            setattr(
                settings,
                backend.setting_fullname("USER_DN_TEMPLATE"),
                values["ldap_user_dn_template"],
            )
            setattr(
                settings, backend.setting_fullname("BIND_AS_AUTHENTICATING_USER"), True
            )
        if values["ldap_is_active_directory"]:
            setting = backend.setting_fullname("GLOBAL_OPTIONS")
            if not hasattr(settings, setting):
                setattr(settings, setting, {ldap.OPT_REFERRALS: False})
            else:
                getattr(settings, setting)[ldap.OPT_REFERRALS] = False

    def to_django_settings(self):
        """Apply LDAP related parameters to Django settings.

        Doing so, we can use the django_auth_ldap module.
        """
        try:
            import ldap  # noqa

            ldap_available = True
        except ImportError:
            ldap_available = False

        values = dict(param_tools.get_global_parameters("core"))
        if not ldap_available or values["authentication_type"] != "ldap":
            return

        from modoboa.lib.authbackends import LDAPBackend

        self._apply_ldap_settings(values, LDAPBackend)

        if not values["ldap_enable_secondary_server"]:
            return

        from modoboa.lib.authbackends import LDAPSecondaryBackend

        self._apply_ldap_settings(values, LDAPSecondaryBackend)

    def save(self):
        """Extra save actions."""
        super().save()
        self.localconfig.need_dovecot_update = True
        self.localconfig.save(update_fields=["need_dovecot_update"])


GLOBAL_PARAMETERS_STRUCT = collections.OrderedDict(
    [
        (
            "authentication",
            {
                "label": gettext_lazy("Authentication"),
                "params": collections.OrderedDict(
                    [
                        (
                            "authentication_type",
                            {
                                "label": gettext_lazy("Authentication type"),
                                "help_text": gettext_lazy(
                                    "The backend used for authentication"
                                ),
                            },
                        ),
                        (
                            "password_scheme",
                            {
                                "label": gettext_lazy("Default password scheme"),
                                "help_text": gettext_lazy(
                                    "Scheme used to crypt mailbox passwords"
                                ),
                            },
                        ),
                        (
                            "rounds_number",
                            {
                                "label": gettext_lazy("Rounds"),
                                "help_text": gettext_lazy(
                                    "Number of rounds to use (only used by sha256crypt and "
                                    "sha512crypt). Must be between 1000 and 999999999, "
                                    "inclusive."
                                ),
                            },
                        ),
                        (
                            "update_scheme",
                            {
                                "label": gettext_lazy(
                                    "Update password scheme at login"
                                ),
                                "help_text": gettext_lazy(
                                    "Update user password at login to use the default "
                                    "password scheme"
                                ),
                            },
                        ),
                        (
                            "default_password",
                            {
                                "label": gettext_lazy("Default password"),
                                "help_text": gettext_lazy(
                                    "Default password for automatically created accounts."
                                ),
                            },
                        ),
                        (
                            "random_password_length",
                            {
                                "label": gettext_lazy("Random password length"),
                                "help_text": gettext_lazy(
                                    "Length of randomly generated passwords."
                                ),
                            },
                        ),
                        (
                            "update_password_url",
                            {
                                "label": gettext_lazy("Update password service URL"),
                                "help_text": gettext_lazy(
                                    "The URL of an external page where users will be able"
                                    " to update their password. It applies only to non local"
                                    " users, ie. those automatically created after a successful"
                                    " external authentication (LDAP, SMTP)."
                                ),
                            },
                        ),
                        (
                            "password_recovery_msg",
                            {
                                "label": gettext_lazy("Password recovery announcement"),
                                "help_text": gettext_lazy(
                                    "A temporary message that will be displayed on the "
                                    "reset password page."
                                ),
                            },
                        ),
                        (
                            "sms_password_recovery",
                            {
                                "label": gettext_lazy(
                                    "Enable password recovery by SMS"
                                ),
                                "help_text": gettext_lazy(
                                    "Enable password recovery by SMS for users who filled "
                                    "a phone number."
                                ),
                            },
                        ),
                        (
                            "sms_provider",
                            {
                                "label": gettext_lazy("SMS provider"),
                                "display": "sms_password_recovery=true",
                                "help_text": gettext_lazy(
                                    "Choose a provider to send password recovery SMS"
                                ),
                            },
                        ),
                        *sms_backends.get_all_backend_structures(),
                    ]
                ),
            },
        ),
        (
            "ldap",
            {
                "label": _("LDAP"),
                "params": collections.OrderedDict(
                    [
                        (
                            "ldap_server_address",
                            {
                                "label": gettext_lazy("Server address"),
                                "help_text": gettext_lazy(
                                    "The IP address or the DNS name of the LDAP server"
                                ),
                            },
                        ),
                        (
                            "ldap_server_port",
                            {
                                "label": gettext_lazy("Server port"),
                                "help_text": gettext_lazy(
                                    "The TCP port number used by the LDAP server"
                                ),
                            },
                        ),
                        (
                            "ldap_enable_secondary_server",
                            {
                                "label": gettext_lazy(
                                    "Enable secondary server (fallback)"
                                ),
                                "help_text": gettext_lazy(
                                    "Enable a secondary LDAP server which will be used "
                                    "if the primary one fails"
                                ),
                            },
                        ),
                        (
                            "ldap_secondary_server_address",
                            {
                                "label": gettext_lazy("Secondary server address"),
                                "display": "ldap_enable_secondary_server=true",
                                "help_text": gettext_lazy(
                                    "The IP address or the DNS name of the seondary LDAP server"
                                ),
                            },
                        ),
                        (
                            "ldap_secondary_server_port",
                            {
                                "label": gettext_lazy("Secondary server port"),
                                "display": "ldap_enable_secondary_server=true",
                                "help_text": gettext_lazy(
                                    "The TCP port number used by the LDAP secondary server"
                                ),
                            },
                        ),
                        (
                            "ldap_secured",
                            {
                                "label": gettext_lazy("Use a secured connection"),
                                "help_text": gettext_lazy(
                                    "Use an SSL/STARTTLS connection to access the LDAP server"
                                ),
                            },
                        ),
                        (
                            "ldap_is_active_directory",
                            {
                                "label": gettext_lazy("Active Directory"),
                                "help_text": gettext_lazy(
                                    "Tell if the LDAP server is an Active Directory one"
                                ),
                            },
                        ),
                        (
                            "ldap_admin_groups",
                            {
                                "label": gettext_lazy("Administrator groups"),
                                "help_text": gettext_lazy(
                                    "Members of those LDAP Posix groups will be created as "
                                    "domain administrators. Use ';' characters to separate "
                                    "groups."
                                ),
                            },
                        ),
                        (
                            "ldap_group_type",
                            {
                                "label": gettext_lazy("Group type"),
                                "help_text": gettext_lazy(
                                    "The LDAP group type to use with your directory."
                                ),
                            },
                        ),
                        (
                            "ldap_groups_search_base",
                            {
                                "label": gettext_lazy("Groups search base"),
                                "help_text": gettext_lazy(
                                    "The distinguished name of the search base used to find "
                                    "groups"
                                ),
                            },
                        ),
                        (
                            "ldap_password_attribute",
                            {
                                "label": gettext_lazy("Password attribute"),
                                "help_text": gettext_lazy(
                                    "The attribute used to store user passwords"
                                ),
                            },
                        ),
                        (
                            "ldap_auth_sep",
                            {
                                "label": gettext_lazy("LDAP authentication settings"),
                                "display": "authentication_type=ldap",
                                "separator": True,
                            },
                        ),
                        (
                            "ldap_auth_method",
                            {
                                "label": gettext_lazy("Authentication method"),
                                "display": "authentication_type=ldap",
                                "help_text": gettext_lazy(
                                    "Choose the authentication method to use"
                                ),
                            },
                        ),
                        (
                            "ldap_bind_dn",
                            {
                                "label": gettext_lazy("Bind DN"),
                                "help_text": gettext_lazy(
                                    "The distinguished name to use when binding to the LDAP "
                                    "server. Leave empty for an anonymous bind"
                                ),
                                "display": "authentication_type=ldap&ldap_auth_method=searchbind",
                            },
                        ),
                        (
                            "ldap_bind_password",
                            {
                                "label": gettext_lazy("Bind password"),
                                "help_text": gettext_lazy(
                                    "The password to use when binding to the LDAP server "
                                    "(with 'Bind DN')"
                                ),
                                "display": "authentication_type=ldap&ldap_auth_method=searchbind",
                                "password": True,
                            },
                        ),
                        (
                            "ldap_search_base",
                            {
                                "label": gettext_lazy("Users search base"),
                                "help_text": gettext_lazy(
                                    "The distinguished name of the search base used to find "
                                    "users"
                                ),
                                "display": "authentication_type=ldap&ldap_auth_method=searchbind",
                            },
                        ),
                        (
                            "ldap_search_filter",
                            {
                                "label": gettext_lazy("Search filter"),
                                "help_text": gettext_lazy(
                                    "An optional filter string (e.g. '(objectClass=person)'). "
                                    "In order to be valid, it must be enclosed in parentheses."
                                ),
                                "display": "authentication_type=ldap&ldap_auth_method=searchbind",
                            },
                        ),
                        (
                            "ldap_user_dn_template",
                            {
                                "label": gettext_lazy("User DN template"),
                                "help_text": gettext_lazy(
                                    "The template used to construct a user's DN. It should "
                                    "contain one placeholder (ie. %(user)s)"
                                ),
                                "display": "authentication_type=ldap&ldap_auth_method=directbind",
                            },
                        ),
                        (
                            "ldap_sync_sep",
                            {
                                "label": gettext_lazy("LDAP synchronization settings"),
                                "separator": True,
                            },
                        ),
                        (
                            "ldap_sync_bind_dn",
                            {
                                "label": gettext_lazy("Bind DN"),
                                "help_text": gettext_lazy(
                                    "The distinguished name to use when binding to the LDAP server. "
                                    "Leave empty for an anonymous bind"
                                ),
                            },
                        ),
                        (
                            "ldap_sync_bind_password",
                            {
                                "label": gettext_lazy("Bind password"),
                                "help_text": gettext_lazy(
                                    "The password to use when binding to the LDAP server "
                                    "(with 'Bind DN')"
                                ),
                                "password": True,
                            },
                        ),
                        (
                            "ldap_enable_sync",
                            {
                                "label": gettext_lazy("Enable export to LDAP"),
                                "help_text": gettext_lazy(
                                    "Enable automatic synchronization between local database "
                                    "and LDAP directory"
                                ),
                            },
                        ),
                        (
                            "ldap_sync_delete_remote_account",
                            {
                                "label": gettext_lazy(
                                    "Delete remote LDAP account when local account is deleted"
                                ),
                                "help_text": gettext_lazy(
                                    "Delete remote LDAP account when local account is deleted, "
                                    "otherwise it will be disabled."
                                ),
                                "display": "ldap_enable_sync=true",
                            },
                        ),
                        (
                            "ldap_sync_account_dn_template",
                            {
                                "label": gettext_lazy("Account DN template"),
                                "help_text": gettext_lazy(
                                    "The template used to construct an account's DN. It should "
                                    "contain one placeholder (ie. %(user)s)"
                                ),
                                "display": "ldap_enable_sync=true",
                            },
                        ),
                        (
                            "ldap_enable_import",
                            {
                                "label": gettext_lazy("Enable import from LDAP"),
                                "help_text": gettext_lazy(
                                    "Enable account synchronization from LDAP directory to "
                                    "local database"
                                ),
                            },
                        ),
                        (
                            "ldap_import_search_base",
                            {
                                "label": gettext_lazy("Users search base"),
                                "help_text": gettext_lazy(
                                    "The distinguished name of the search base used to find "
                                    "users"
                                ),
                                "display": "ldap_enable_import=true",
                            },
                        ),
                        (
                            "ldap_import_search_filter",
                            {
                                "label": gettext_lazy("Search filter"),
                                "help_text": gettext_lazy(
                                    "An optional filter string (e.g. '(objectClass=person)'). "
                                    "In order to be valid, it must be enclosed in parentheses."
                                ),
                                "display": "ldap_enable_import=true",
                            },
                        ),
                        (
                            "ldap_import_username_attr",
                            {
                                "label": gettext_lazy("Username attribute"),
                                "help_text": gettext_lazy(
                                    "The name of the LDAP attribute where the username can be "
                                    "found."
                                ),
                                "display": "ldap_enable_import=true",
                            },
                        ),
                        (
                            "ldap_dovecot_sync",
                            {
                                "label": gettext_lazy("Enable Dovecot LDAP sync"),
                                "help_text": gettext_lazy(
                                    "LDAP authentication settings will be applied to Dovecot "
                                    "configuration."
                                ),
                            },
                        ),
                        (
                            "ldap_dovecot_conf_file",
                            {
                                "label": gettext_lazy("Dovecot LDAP config file"),
                                "help_text": gettext_lazy(
                                    "Location of the configuration file which contains "
                                    "Dovecot LDAP settings."
                                ),
                                "display": "ldap_dovecot_sync=true",
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "dashboard",
            {
                "label": gettext_lazy("Dashboard"),
                "params": collections.OrderedDict(
                    [
                        (
                            "rss_feed_url",
                            {
                                "label": gettext_lazy("Custom RSS feed"),
                                "help_text": gettext_lazy(
                                    "Display custom RSS feed to resellers and domain "
                                    "administrators"
                                ),
                            },
                        ),
                        (
                            "hide_features_widget",
                            {
                                "label": gettext_lazy("Hide features widget"),
                                "help_text": gettext_lazy(
                                    "Hide features widget for resellers and domain "
                                    "administrators"
                                ),
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "notifications",
            {
                "label": gettext_lazy("Notifications"),
                "params": collections.OrderedDict(
                    [
                        (
                            "sender_address",
                            {
                                "label": gettext_lazy("Sender address"),
                                "help_text": gettext_lazy(
                                    "Email address used to send notifications."
                                ),
                            },
                        )
                    ]
                ),
            },
        ),
        (
            "api",
            {
                "label": gettext_lazy("Public API"),
                "params": collections.OrderedDict(
                    [
                        (
                            "enable_api_communication",
                            {
                                "label": gettext_lazy("Enable communication"),
                                "help_text": gettext_lazy(
                                    "Automatically checks if a newer version is available"
                                ),
                            },
                        ),
                        (
                            "check_new_versions",
                            {
                                "label": gettext_lazy("Check new versions"),
                                "display": "enable_api_communication=true",
                                "help_text": gettext_lazy(
                                    "Automatically checks if a newer version is available"
                                ),
                            },
                        ),
                        (
                            "send_new_versions_email",
                            {
                                "label": gettext_lazy(
                                    "Send an email when new versions are found"
                                ),
                                "display": "check_new_versions=true",
                                "help_text": gettext_lazy(
                                    "Send an email to notify admins about new versions"
                                ),
                            },
                        ),
                        (
                            "new_versions_email_rcpt",
                            {
                                "label": gettext_lazy("Recipient"),
                                "display": "check_new_versions=true",
                                "help_text": gettext_lazy(
                                    "Recipient of new versions notification emails."
                                ),
                            },
                        ),
                        (
                            "send_statistics",
                            {
                                "label": gettext_lazy("Send statistics"),
                                "display": "enable_api_communication=true",
                                "help_text": gettext_lazy(
                                    "Send statistics to Modoboa public API "
                                    "(counters and used extensions)"
                                ),
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "misc",
            {
                "label": gettext_lazy("Miscellaneous"),
                "params": collections.OrderedDict(
                    [
                        (
                            "enable_inactive_accounts",
                            {
                                "label": gettext_lazy(
                                    "Enable inactive account tracking"
                                ),
                                "help_text": gettext_lazy(
                                    "Allow the administrator to set a threshold (in days) "
                                    "beyond which an account is considered inactive "
                                    "if the user hasn't logged in"
                                ),
                            },
                        ),
                        (
                            "inactive_account_threshold",
                            {
                                "label": gettext_lazy("Inactive account threshold"),
                                "display": "enable_inactive_accounts=true",
                                "help_text": gettext_lazy(
                                    "An account with a last login date greater than this "
                                    "threshold (in days) will be considered as inactive"
                                ),
                            },
                        ),
                        (
                            "top_notifications_check_interval",
                            {
                                "label": gettext_lazy(
                                    "Top notifications check interval"
                                ),
                                "help_text": gettext_lazy(
                                    "Interval between two top notification checks (in seconds)"
                                ),
                            },
                        ),
                        (
                            "log_maximum_age",
                            {
                                "label": gettext_lazy("Maximum log record age"),
                                "help_text": gettext_lazy(
                                    "The maximum age in days of a log record"
                                ),
                            },
                        ),
                        (
                            "items_per_page",
                            {
                                "label": gettext_lazy("Items per page"),
                                "help_text": gettext_lazy(
                                    "Number of displayed items per page"
                                ),
                            },
                        ),
                        (
                            "default_top_redirection",
                            {
                                "label": gettext_lazy("Default top redirection"),
                                "help_text": gettext_lazy(
                                    "The default redirection used when no application is "
                                    "specified"
                                ),
                            },
                        ),
                    ]
                ),
            },
        ),
    ]
)
