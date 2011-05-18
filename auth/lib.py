# coding: utf-8

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

