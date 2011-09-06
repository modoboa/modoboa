# coding: utf-8

import crypt, hashlib
import string
from random import Random
from Crypto.Cipher import AES
import base64
from modoboa.lib import parameters

def encrypt(clear):
    obj = AES.new(parameters.get_admin("SECRET_KEY"),
                  AES.MODE_ECB)
    if len(clear) % AES.block_size:
        clear += "\0" * (AES.block_size - len(clear) % AES.block_size)
    ciph = obj.encrypt(clear)
    ciph = base64.b64encode(ciph)
    return ciph

def decrypt(ciph):
    obj = AES.new(parameters.get_admin("SECRET_KEY"), AES.MODE_ECB)
    ciph = base64.b64decode(ciph)
    clear = obj.decrypt(ciph)
    return clear.rstrip('\0')

def get_password(request):
    return decrypt(request.session["password"])

def _check_password(password, crypted):
    scheme = parameters.get_admin("PASSWORD_SCHEME", app="admin")
    if scheme == "crypt":
        return crypt.crypt(password, crypted) == crypted
    if scheme == "md5":
        return hashlib.md5(password).hexdigest() == crypted
    return password

def crypt_password(password):
    scheme = parameters.get_admin("PASSWORD_SCHEME", app="admin")
    if scheme == "crypt":
        salt = ''.join(Random().sample(string.letters + string.digits, 2))
        return crypt.crypt(password, salt)
    if scheme == "md5":
        return hashlib.md5(password).hexdigest()
    return password
