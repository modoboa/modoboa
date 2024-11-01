"""Core settings."""

import collections

from django.core.cache import cache
from django.utils.translation import gettext as _, gettext_lazy

from modoboa.core.password_hashers.utils import cache_available_password_hasher

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
                            "allow_special_characters",
                            {
                                "label": gettext_lazy("Allow special characters for random password"),
                                "help_text": gettext_lazy(
                                    "Enable special characters in randomly generated "
                                    "passwords."
                                ),
                            }
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
