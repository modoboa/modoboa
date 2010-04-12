from django.contrib.auth.models import User
from mailng.admin.models import Mailbox
from django.conf import settings
import hashlib
import crypt
import string
from random import Random

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
        if not check_password(password, mb.password):
            return None
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

def __get_password_scheme():
    try:
        scheme = getattr(settings, "PASSWORD_SCHEME")
    except AttributeError:
        scheme = "crypt"
    return scheme

def check_password(password, crypted):
    scheme = __get_password_scheme()
    if scheme == "crypt":
        return crypt.crypt(password, crypted) == crypted
    if scheme == "md5":
        return hashlib.md5(password).hexdigest() == crypted
    return password

def crypt_password(password):
    scheme = __get_password_scheme()
    if scheme == "crypt":
        salt = ''.join(Random().sample(string.letters + string.digits, 2))
        return crypt.crypt(password, salt)
    if scheme == "md5":
        return hashlib.md5(password).hexdigest()
    return password
