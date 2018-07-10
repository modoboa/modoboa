# -*- coding: utf-8 -*-

"""Custom authentication backends."""

from __future__ import unicode_literals

import smtplib

from django.conf import settings

from modoboa.core.models import User, populate_callback
from modoboa.lib.email_utils import split_mailbox
from modoboa.parameters import tools as param_tools


class SMTPBackend(object):
    """A backend to authenticate against an SMTP server."""

    def authenticate(self, request, username=None, password=None):
        """Check the username/password and return a User."""
        host = getattr(settings, "AUTH_SMTP_SERVER_ADDRESS", "localhost")
        port = getattr(settings, "AUTH_SMTP_SERVER_PORT", 25)
        secured_mode = getattr(settings, "AUTH_SMTP_SECURED_MODE", None)
        if secured_mode == "ssl":
            smtp = smtplib.SMTP_SSL(host, port)
        else:
            smtp = smtplib.SMTP(host, port)
            if secured_mode == "starttls":
                smtp.starttls()
        try:
            smtp.login(username, password)
        except smtplib.SMTPException:
            return None
        return self.get_or_build_user(username)

    def get_or_build_user(self, username):
        """Get a user or create it the first time.

        .. note::

           We assume the username is a valid email address.
        """
        user, created = User.objects.get_or_create(
            username__iexact=username, defaults={
                "username": username.lower(),
                "email": username.lower(),
                "language": settings.LANGUAGE_CODE
            }
        )
        if created:
            populate_callback(user)
        return user

    def get_user(self, user_pk):
        """Retrieve a User instance."""
        user = None
        try:
            user = User.objects.get(pk=user_pk)
        except User.DoesNotExist:
            pass
        return user


try:
    from django_auth_ldap.backend import (
        LDAPBackend as orig_LDAPBackend, _LDAPUser
    )

    class LDAPBackend(orig_LDAPBackend):

        def __init__(self, *args, **kwargs):
            """Load LDAP settings."""
            param_tools.apply_to_django_settings()
            super(LDAPBackend, self).__init__(*args, **kwargs)
            self.global_params = dict(
                param_tools.get_global_parameters("core"))

        def get_or_build_user(self, username, ldap_user):
            """
            This must return a (User, created) 2-tuple for the given
            LDAP user.  username is the Django-friendly username of
            the user. ldap_user.dn is the user's DN and
            ldap_user.attrs contains all of their LDAP attributes.
            """
            group = "SimpleUsers"
            admin_groups = self.global_params["ldap_admin_groups"].split(";")
            for grp in admin_groups:
                if grp.strip() in ldap_user.group_names:
                    group = "DomainAdmins"
                    break
            if group == "SimpleUsers":
                lpart, domain = split_mailbox(username)
                if domain is None:
                    return None
            user, created = User.objects.get_or_create(
                username__iexact=username,
                defaults={
                    "username": username.lower(),
                    "is_local": False,
                    "language": settings.LANGUAGE_CODE
                }
            )
            if created:
                populate_callback(user, group)
            return user, created

        def get_user(self, user_id):
            user = None
            try:
                user = User.objects.get(pk=user_id)
                _LDAPUser(self, user=user)  # This sets user.ldap_user
            except User.DoesNotExist:
                pass
            return user

        def authenticate(self, *args, **kwargs):
            if self.global_params["authentication_type"] == "ldap":
                return super(LDAPBackend, self).authenticate(*args, **kwargs)
            return None

except ImportError:
    pass
