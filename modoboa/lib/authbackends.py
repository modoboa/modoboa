"""Custom authentication backends."""

from django.contrib.auth.backends import ModelBackend

from modoboa.core.models import User
from modoboa.lib import parameters
from modoboa.lib.email_utils import split_mailbox


class SimpleBackend(ModelBackend):

    """Simple authentication backend."""

    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        if not user.check_password(password):
            return None
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

try:
    from django_auth_ldap.backend import (
        LDAPBackend as orig_LDAPBackend, _LDAPUser
    )
    from modoboa.core.models import populate_callback

    class LDAPBackend(orig_LDAPBackend):

        def __init__(self, *args, **kwargs):
            """Load LDAP settings."""
            parameters.apply_to_django_settings()
            super(LDAPBackend, self).__init__(*args, **kwargs)

        def get_or_create_user(self, username, ldap_user):
            """
            This must return a (User, created) 2-tuple for the given
            LDAP user.  username is the Django-friendly username of
            the user. ldap_user.dn is the user's DN and
            ldap_user.attrs contains all of their LDAP attributes.
            """
            group = 'SimpleUsers'
            admin_groups = parameters \
                .get_admin('LDAP_ADMIN_GROUPS', app='core').split(';')
            for grp in admin_groups:
                if grp.strip() in ldap_user.group_names:
                    group = 'DomainAdmins'
                    break
            if group == 'SimpleUsers':
                lpart, domain = split_mailbox(username)
                if domain is None:
                    return None
            user, created = User.objects.get_or_create(
                username__iexact=username,
                defaults={'username': username.lower(), 'is_local': False}
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

        def authenticate(self, username, password):
            auth_type = parameters.get_admin("AUTHENTICATION_TYPE", app="core")
            if auth_type == "ldap":
                return super(LDAPBackend, self).authenticate(
                    username, password)
            return None

except ImportError:
    pass
