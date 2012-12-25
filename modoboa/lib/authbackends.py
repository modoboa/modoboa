from django.contrib.auth.backends import ModelBackend
from modoboa.admin.models import User

class SimpleBackend(ModelBackend):

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
    from django_auth_ldap.backend import LDAPBackend as orig_LDAPBackend, _LDAPUser
    from modoboa.admin.models import User

    class LDAPBackend(orig_LDAPBackend):

        def get_or_create_user(self, username, ldap_user):
            """
            This must return a (User, created) 2-tuple for the given LDAP user.
            username is the Django-friendly username of the user. ldap_user.dn is
            the user's DN and ldap_user.attrs contains all of their LDAP attributes.
            """
            return User.objects.get_or_create(
                username__iexact=username, 
                defaults={'username': username.lower()}
                )

        def get_user(self, user_id):
            user = None

            try:
                user = User.objects.get(pk=user_id)
                _LDAPUser(self, user=user) # This sets user.ldap_user
            except User.DoesNotExist:
                pass

            return user

except ImportError:
    pass
