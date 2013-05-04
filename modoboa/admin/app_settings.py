from django import forms
from django.utils.translation import ugettext as _, ugettext_lazy
from modoboa.lib.formutils import YesNoField, SeparatorField, InlineRadioSelect
from modoboa.lib.sysutils import exec_cmd
from modoboa.lib import parameters


def enabled_applications():
    """Return the list of currently enabled extensions

    We check if the table exists before trying to fetch activated
    extensions because the admin module is always imported by Django,
    even before the database exists (example: the first ``syncdb``).

    :return: a list
    """
    from modoboa.admin.models import Extension
    from modoboa.lib.dbutils import db_table_exists

    result = [("admin", "admin"), ("userprefs", "userprefs")]
    if db_table_exists("admin_extension"):
        exts = Extension.objects.filter(enabled=True)
        result += [(ext.name, ext.name) for ext in exts]
    return sorted(result, key=lambda e: e[0])


class GeneralParametersForm(parameters.AdminParametersForm):
    app = "admin"

    sep1 = SeparatorField(label=ugettext_lazy("Authentication"))

    authentication_type = forms.ChoiceField(
        label=ugettext_lazy("Authentication type"),
        choices=[('local', ugettext_lazy("Local")),
                 ('ldap', "LDAP")],
        initial="local",
        help_text=ugettext_lazy("The backend used for authentication"),
        widget=InlineRadioSelect
    )

    password_scheme = forms.ChoiceField(
        label=ugettext_lazy("Default password scheme"),
        choices=[("crypt", "crypt"),
                 ("md5", "md5"),
                 ("md5crypt", "md5crypt"),
                 ("sha256", "sha256"),
                 ("plain", "plain")],
        initial="md5crypt",
        help_text=ugettext_lazy("Scheme used to crypt mailbox passwords")
    )

    secret_key = forms.CharField(
        label=ugettext_lazy("Secret key"),
        initial="abcdefghijklmnop",
        help_text=ugettext_lazy("Key used to encrypt/decrypt passwords")
    )

    # LDAP specific settings
    ldap_sep = SeparatorField(label=ugettext_lazy("LDAP settings"))

    ldap_server_address = forms.CharField(
        label=ugettext_lazy("Server address"),
        initial="localhost",
        help_text=ugettext_lazy("The IP address of the DNS name of the LDAP server")
    )

    ldap_server_port = forms.IntegerField(
        label=ugettext_lazy("Server port"),
        initial=389,
        help_text=ugettext_lazy("The TCP port number used by the LDAP server")
    )

    ldap_secured = YesNoField(
        label=ugettext_lazy("Use a secured connection"),
        initial="no",
        help_text=ugettext_lazy("Use an SSL/TLS connection to access the LDAP server")
    )

    ldap_auth_method = forms.ChoiceField(
        label=ugettext_lazy("Authentication method"),
        choices=[('searchbind', ugettext_lazy("Search and bind")),
                 ('directbind', ugettext_lazy("Direct bind"))],
        initial='searchbind',
        help_text=ugettext_lazy("Choose the authentication method to use"),
        widget=InlineRadioSelect
    )

    ldap_bind_dn = forms.CharField(
        label=ugettext_lazy("Bind DN"),
        initial='',
        help_text=ugettext_lazy("The distinguished name to use when binding to the LDAP server. Leave empty for an anonymous bind"),
        required=False
    )

    ldap_bind_password = forms.CharField(
        label=ugettext_lazy("Bind password"),
        initial='',
        help_text=ugettext_lazy("The password to use when binding to the LDAP server (with 'Bind DN')"),
        widget=forms.PasswordInput,
        required=False
    )

    ldap_search_base = forms.CharField(
        label=ugettext_lazy("Search base"),
        initial="",
        help_text=ugettext_lazy("The distinguished name of the search base"),
        required=False
    )

    ldap_search_filter = forms.CharField(
        label=ugettext_lazy("Search filter"),
        initial="(mail=%(user)s)",
        help_text=ugettext_lazy("An optional filter string (e.g. '(objectClass=person)'). In order to be valid, it must be enclosed in parentheses."),
        required=False
    )

    ldap_user_dn_template = forms.CharField(
        label=ugettext_lazy("User DN template"),
        initial="",
        help_text=ugettext_lazy("The template used to construct a user's DN. It should contain one placeholder (ie. %(user)s)"),
        required=False
    )

    ldap_password_attribute = forms.CharField(
        label=ugettext_lazy("Password attribute"),
        initial="userPassword",
        help_text=ugettext_lazy("The attribute used to store user passwords")
    )

    ldap_is_active_directory = YesNoField(
        label=ugettext_lazy("Active Directory"),
        initial="no",
        help_text=ugettext_lazy("Tell if the LDAP server is an Active Directory one")
    )

    sep2 = SeparatorField(label=ugettext_lazy("Mailboxes"))

    handle_mailboxes = YesNoField(
        label=ugettext_lazy("Handle mailboxes on filesystem"),
        initial="no",
        help_text=ugettext_lazy("Rename or remove mailboxes on the filesystem when they get renamed or removed within Modoboa")
    )

    mailboxes_owner = forms.CharField(
        label=ugettext_lazy("Mailboxes ower"),
        initial="vmail",
        help_text=ugettext_lazy("The UNIX account who owns mailboxes on the filesystem")
    )

    auto_account_removal = YesNoField(
        label=ugettext_lazy("Automatic account removal"),
        initial="no",
        help_text=ugettext_lazy("When a mailbox is removed, also remove the associated account"),
    )

    sep3 = SeparatorField(label=ugettext_lazy("Miscellaneous"))

    items_per_page = forms.IntegerField(
        label=ugettext_lazy("Items per page"),
        initial=30,
        help_text=ugettext_lazy("Number of displayed items per page")
    )

    default_top_redirection = forms.ChoiceField(
        label=ugettext_lazy("Default top redirection"),
        choices=[],
        initial="admin",
        help_text=ugettext_lazy("The default redirection used when no application is specified")
    )

    # Visibility rules
    visibility_rules = {
        "mailboxes_owner": "handle_mailboxes=yes",
        "ldap_sep": "authentication_type=ldap",
        "ldap_server_address": "authentication_type=ldap",
        "ldap_server_port": "authentication_type=ldap",
        "ldap_secured": "authentication_type=ldap",
        "ldap_auth_method": "authentication_type=ldap",
        "ldap_bind_dn": "ldap_auth_method=searchbind",
        "ldap_bind_password": "ldap_auth_method=searchbind",
        "ldap_search_base": "ldap_auth_method=searchbind",
        "ldap_search_filter": "ldap_auth_method=searchbind",
        "ldap_user_dn_template": "ldap_auth_method=directbind",
        "ldap_password_attribute": "authentication_type=ldap",
        "ldap_is_active_directory": "authentication_type=ldap"
    }

    def __init__(self, *args, **kwargs):
        super(GeneralParametersForm, self).__init__(*args, **kwargs)
        self.fields["default_top_redirection"].choices = enabled_applications()
        hide_fields = False
        try:
            code, version = exec_cmd("dovecot --version")
        except OSError, e:
            hide_fields = True
        else:
            if code or not version.strip().startswith("2"):
                hide_fields = True
        if hide_fields:
            del self.fields["handle_mailboxes"]
            del self.fields["mailboxes_owner"]

    def clean(self):
        """Custom validation method

        Depending on 'ldap_auth_method' value, we check for different
        required parameters.
        """
        super(GeneralParametersForm, self).clean()
        if len(self._errors):
            raise forms.ValidationError(self._errors)
        cleaned_data = self.cleaned_data
        if cleaned_data["authentication_type"] != "ldap":
            return cleaned_data

        if cleaned_data["ldap_auth_method"] == "searchbind":
            required_fields = ["ldap_search_base", "ldap_search_filter"]
        else:
            required_fields = ["ldap_user_dn_template"]
            
        for f in required_fields:
            if not f in cleaned_data or cleaned_data[f] == u'':
                self._errors[f] = self.error_class([_("This field is required")])

        return cleaned_data

    def to_django_settings(self):
        """Apply LDAP related parameters to Django settings

        Doing so, we can use the django_auth_ldap module.
        """
        from django.conf import settings
        try:
            import ldap
            from django_auth_ldap.config import LDAPSearch
            ldap_available = True
        except ImportError:
            ldap_available = False

        values = self.get_current_values()
        if not ldap_available or values["authentication_type"] != "ldap":
            return
        if not hasattr(settings, "AUTH_LDAP_USER_ATTR_MAP"):
            setattr(settings, "AUTH_LDAP_USER_ATTR_MAP", {
                "first_name": "givenName",
                "email": "mail",
                "last_name": "sn"
            })
        ldap_uri = 'ldaps://' if values["ldap_secured"] == "yes" else "ldap://"
        ldap_uri += "%s:%s" % (values["ldap_server_address"], values["ldap_server_port"])
        setattr(settings, "AUTH_LDAP_SERVER_URI", ldap_uri)
        if values["ldap_auth_method"] == "searchbind":
            setattr(settings, "AUTH_LDAP_BIND_DN", values["ldap_bind_dn"])
            setattr(settings, "AUTH_LDAP_BIND_PASSWORD", values["ldap_bind_password"])
            search = LDAPSearch(
                values["ldap_search_base"], ldap.SCOPE_SUBTREE,
                values["ldap_search_filter"]
            )
            setattr(settings, "AUTH_LDAP_USER_SEARCH", search)
        else:
            setattr(settings, "AUTH_LDAP_USER_DN_TEMPLATE", values["ldap_user_dn_template"])

        if values["ldap_is_active_directory"] == "yes":
            if not hasattr(settings, "AUTH_LDAP_GLOBAL_OPTIONS"):
                setattr(settings, "AUTH_LDAP_GLOBAL_OPTIONS", {
                    ldap.OPT_REFERRALS: False
                })
            else:
                settings.AUTH_LDAP_GLOBAL_OPTIONS[ldap.OPT_REFERRALS] = False
