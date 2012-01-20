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
import sys
import ldap
import re
import base64
from django.conf import settings
from modoboa.auth.lib import crypt_password
from modoboa.lib import parameters

class LDAPException(Exception): pass

class LDAPAuthBackend(object):
    def __init__(self):
        self.server_uri = self._setting("AUTH_LDAP_SERVER_URI", "ldap://localhost")
        self.user_base = self._setting("LDAP_USER_BASE", "")
        self.user_filter = self._setting("LDAP_USER_FILTER", "")
        self.bind_dn = self._setting("AUTH_LDAP_BIND_DN", "")
        self.bind_pwd = self._setting("AUTH_LDAP_BIND_PASSWORD", "")
        self.pwd_attr = self._setting("LDAP_PASSWORD_ATTR", "userPassword")
        self.ldap_ad = self._setting("LDAP_ACTIVE_DIRECTORY", False)

        self.conn = self._get_conn(self.bind_dn, self.bind_pwd)

    def _setting(self, name, default):
        try:
            value = getattr(settings, name)
        except AttributeError:
            value = default
        return value

    def _get_conn(self, bind_dn, bind_pwd):
        conn = ldap.initialize(self.server_uri)
	conn.set_option(ldap.OPT_X_TLS_DEMAND, True)
	conn.set_option(ldap.OPT_DEBUG_LEVEL, 255)
        conn.simple_bind_s(bind_dn, bind_pwd)
        return conn

    def _expand_filter(self, rawvalue, **kwargs):
        return rawvalue % kwargs

    def _find_user_dn(self, user):
        filtr = self._expand_filter(self.user_filter, user=user)
        res = self.conn.search_s(self.user_base, ldap.SCOPE_SUBTREE, filtr)
        try:
            dn = res[0][0]
        except IndexError:
            return None
        return dn

    def _crypt_password(self, clearpassword):
        """Overidding of the crypt_password function (LDAP compliant)

        The crypted password in base64 encoded and we prepend the used
        algorithm to the returned value. (between {})
        
        :param clearpassword: the clear password
        :return: the encrypted password
        """
        scheme = parameters.get_admin("PASSWORD_SCHEME", app="admin")
        if scheme == "clear":
            return str(clearpassword)
        crypted = crypt_password(clearpassword, False)
        return str("{%s}%s" % (scheme.upper(), base64.encodestring(crypted)))

    def update_user_password(self, user, password, newpassword):
        try:
            dn = self._find_user_dn(user)
            conn = self._get_conn(dn, password)
            if self.ldap_ad:
                newpassword = ('"%s"' % newpassword).encode('utf-16').lstrip('\377\376')
            ldif = [(ldap.MOD_REPLACE,
                     self.pwd_attr, 
                     self._crypt_password(newpassword))]
            conn.modify_s(dn, ldif)
        except ldap.LDAPError, e:
            raise LDAPException(str(e))


