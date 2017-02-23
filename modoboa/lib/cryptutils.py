# coding: utf-8
"""Crypto related utilities."""

import base64
import random
import string

from Crypto.Cipher import AES

from modoboa.parameters import tools as param_tools


def random_key(l=16):
    """Generate a random key.

    :param integer l: the key's length
    :return: a string
    """
    punctuation = """!#$%&'()*+,-./:;<=>?@[]^_`{|}~"""
    population = string.digits + string.letters + punctuation
    while True:
        key = "".join(random.sample(population * l, l))
        if len(key) == l:
            return key


def encrypt(clear):
    key = param_tools.get_global_parameter("secret_key", app="core")
    obj = AES.new(key, AES.MODE_ECB)
    if type(clear) is unicode:
        clear = clear.encode("utf-8")
    if len(clear) % AES.block_size:
        clear += " " * (AES.block_size - len(clear) % AES.block_size)
    ciph = obj.encrypt(clear)
    ciph = base64.b64encode(ciph)
    return ciph


def decrypt(ciph):
    obj = AES.new(
        param_tools.get_global_parameter(
            "secret_key", app="core"), AES.MODE_ECB
    )
    ciph = base64.b64decode(ciph)
    clear = obj.decrypt(ciph)
    return clear.rstrip(' ')


def get_password(request):
    return decrypt(request.session["password"])
