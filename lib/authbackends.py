from django.contrib.auth.models import User
from modoboa.admin.models import Mailbox
from modoboa.lib import _check_password

class SimpleBackend:

    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False

    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        try:
            mb = user.mailbox_set.all()[0]
        except Exception:
            return None
        if not _check_password(password, mb.password):
            return None
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

