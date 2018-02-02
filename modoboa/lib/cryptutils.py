# -*- coding: utf-8 -*-

"""Crypto related utilities."""

from __future__ import unicode_literals

import base64

from cryptography.fernet import Fernet

from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils.encoding import smart_bytes, smart_text


def random_key(length=16):
    """Generate a new key used to encrypt user passwords in session storage."""
    chars = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
    return get_random_string(length, chars)


def _get_fernet():
    """Create a Fernet instance."""
    secret_key = base64.urlsafe_b64encode(smart_bytes(settings.SECRET_KEY[:32]))
    return Fernet(secret_key)


def encrypt(clear_value):
    """Encrypt a value using secret_key."""
    return smart_text(_get_fernet().encrypt(smart_bytes(clear_value)))


def decrypt(encrypted_value):
    """Decrypt a value using secret_key."""
    return smart_text(_get_fernet().decrypt(smart_bytes(encrypted_value)))


def get_password(request):
    """
    Retrieve and decrypt the users password from session storage.

    This is used by modoboa-webmail to allow the user to send/receive e-mails
    without having to ask the user for a password on each connection to the
    postfix/dovecot server.
    """
    try:
        return decrypt(request.session["password"])
    except KeyError:
        return None
