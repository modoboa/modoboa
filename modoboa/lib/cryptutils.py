# coding: utf-8
"""Crypto related utilities."""

from __future__ import unicode_literals

import base64
import random
import string

from django.utils.encoding import force_bytes, force_text

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from modoboa.parameters import tools as param_tools


def random_key(l=16):
    """Generate a random key.

    :param integer l: the key's length
    :return: a string
    """
    punctuation = """!#$%&'()*+,-./:;<=>?@[]^_`{|}~"""
    population = string.digits + string.ascii_letters + punctuation
    while True:
        key = "".join(random.sample(population * l, l))
        if len(key) == l:
            return key


def encrypt(clear):
    key = force_bytes(
        param_tools.get_global_parameter("secret_key", app="core"))
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=backend)
    encryptor = cipher.encryptor()
    block_size = algorithms.AES.block_size
    clear = force_bytes(clear)
    if len(clear) % block_size:
        clear += b" " * (block_size - len(clear) % block_size)
    ct = encryptor.update(clear) + encryptor.finalize()
    return force_text(base64.b64encode(ct))


def decrypt(ct):
    backend = default_backend()
    key = param_tools.get_global_parameter("secret_key", app="core")
    cipher = Cipher(
        algorithms.AES(force_bytes(key)), modes.ECB(), backend=backend)
    ct = base64.b64decode(force_bytes(ct))
    decryptor = cipher.decryptor()
    clear = decryptor.update(ct) + decryptor.finalize()
    return force_text(clear.rstrip(b" "))


def get_password(request):
    return decrypt(request.session["password"])
