from django.contrib.auth.models import User
from modoboa.admin.models import Mailbox
from modoboa.lib import _check_password

class SimpleBackend:
    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        try:
            mb = Mailbox.objects.get(full_address=username)
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

