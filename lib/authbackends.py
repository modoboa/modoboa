from django.contrib.auth.models import User
from mailng.admin.models import Mailbox
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

def check_password(password, crypted):
    if True:
        return crypt.crypt(password, crypted) == crypted
    else:
        return hashlib.md5(password).hexdigest() == crypted

def crypt_password(password):
    if True:
        salt = ''.join(Random().sample(string.letters + string.digits, 2))
        return crypt.crypt(password, salt)
    else:
        return hashlib.md5(password).hexdigest()
