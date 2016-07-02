# coding: utf-8

"""
:mod:`ldaputils` --- a collection of LDAP based classes/functions
-----------------------------------------------------------------

For a first version, the LDAP support offered by Modoboa only supports
one global server definition : the one the django-auth-ldap uses.

Extra information about Active Directory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extracted from `this blog
<http://www.dirmgr.com/blog/2010/8/26/ldap-password-changes-in-active-directory.html>`_:

- Active Directory doesn't appear to support the password modify
  extended operation, so you must change passwords using a normal LDAP
  modify operation.

- Active Directory stores passwords in the unicodePwd attribute,
  rather than userPassword.

- Active Directory will only accept password changes over secure
  connections. I have only ever used SSL. It may be that you can also
  use StartTLS, or perhaps SASL with confidentiality, but I'm not sure
  about that.

- The new password must be enclosed in quotation marks, and it must
  use a UTF-16 little-endian encoding.

- Active Directory may impose some strength requirements on the
  password, although exactly what those requirements are may vary from
  one instance to another.

"""
import ldap

from django.conf import settings
from django.utils.translation import ugettext as _

from modoboa.core.password_hashers import get_password_hasher
from modoboa.lib import parameters
from modoboa.lib.exceptions import InternalError


class LDAPAuthBackend(object):

    def __init__(self):
        parameters.apply_to_django_settings()
        self.server_uri = self._setting(
            "AUTH_LDAP_SERVER_URI", "ldap://localhost"
        )
        self.pwd_attr = self._setting("LDAP_PASSWORD_ATTR", "userPassword")
        self.ldap_ad = self._setting("LDAP_ACTIVE_DIRECTORY", False)
        self.conn = None
        self.user_filter = self._setting("LDAP_USER_FILTER", "")

    def _setting(self, name, default):
        try:
            value = getattr(settings, name)
        except AttributeError:
            value = default
        return value

    def _get_conn(self, dn, password):
        """Get a connection from the server."""
        conn = ldap.initialize(self.server_uri)
        conn.set_option(ldap.OPT_X_TLS_DEMAND, True)
        conn.set_option(ldap.OPT_DEBUG_LEVEL, 255)
        conn.simple_bind_s(dn, password)
        return conn

    def connect_to_server(self, user, password):
        """Connect to the server according to configuration."""
        if self.conn is not None:
            return
        mode = parameters.get_admin("LDAP_AUTH_METHOD", app="core")
        if mode == "searchbind":
            bind_dn = self._setting("AUTH_LDAP_BIND_DN", "")
            bind_pwd = self._setting("AUTH_LDAP_BIND_PASSWORD", "")
            self.conn = self._get_conn(bind_dn, bind_pwd)
        else:
            tpl = self._setting("AUTH_LDAP_USER_DN_TEMPLATE", "")
            self.user_dn = tpl % {"user": user}
            self.conn = self._get_conn(self.user_dn, password)

    def _find_user_dn(self, user):
        """Find the DN of the given user."""
        sbase = parameters.get_admin("LDAP_SEARCH_BASE", app="core")
        sfilter = parameters.get_admin("LDAP_SEARCH_FILTER", app="core")
        sfilter = sfilter % {"user": user}
        res = self.conn.search_s(sbase, ldap.SCOPE_SUBTREE, sfilter)
        try:
            dn = res[0][0]
        except IndexError:
            return None
        return dn

    def _crypt_password(self, clearpassword):
        """Overidding of the crypt_password function (LDAP compliant)

        :param clearpassword: the clear password
        :return: the encrypted password
        """
        scheme = parameters.get_admin("PASSWORD_SCHEME", app="core")
        hasher = get_password_hasher(scheme.upper())('ldap')
        return hasher.encrypt(clearpassword)

    def update_user_password(self, user, password, newpassword):
        """Update user password."""
        self.connect_to_server(user, password)
        user_dn = self._find_user_dn(user)
        if self.ldap_ad:
            newpassword = (
                ('"%s"' % newpassword).encode('utf-16').lstrip('\377\376')
            )
        ldif = [(ldap.MOD_REPLACE,
                 self.pwd_attr,
                 self._crypt_password(newpassword))]
        try:
            self.conn.modify_s(user_dn, ldif)
        except ldap.LDAPError as e:
            raise InternalError(
                _("Failed to update password: {}").format(e))
