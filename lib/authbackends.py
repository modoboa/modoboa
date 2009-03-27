from django.contrib.auth.models import User
from mailng.admin.models import Mailbox
import md5

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
        if mb.password != md5.new(password).hexdigest():
            return None
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
