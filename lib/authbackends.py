from django.contrib.auth.models import User
from mailng.admin.models import Mailbox
import hashlib
import crypt
import string
from random import Random
from mailng.lib import parameters

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

def _check_password(password, crypted):
    scheme = parameters.get_admin("admin", "PASSWORD_SCHEME")
    if scheme == "crypt":
        return crypt.crypt(password, crypted) == crypted
    if scheme == "md5":
        return hashlib.md5(password).hexdigest() == crypted
    return password

def crypt_password(password):
    scheme = parameters.get_admin("admin", "PASSWORD_SCHEME")
    if scheme == "crypt":
        salt = ''.join(Random().sample(string.letters + string.digits, 2))
        return crypt.crypt(password, salt)
    if scheme == "md5":
        return hashlib.md5(password).hexdigest()
    return password
