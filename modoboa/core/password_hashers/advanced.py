# -*- coding: utf-8 -*-

"""
Advanced (ie. stronger) password hashers.

This module relies on `passlib` to provide more secure hashers.
"""

from __future__ import unicode_literals

from passlib.hash import bcrypt, md5_crypt, sha256_crypt, sha512_crypt

from modoboa.parameters import tools as param_tools
from .base import PasswordHasher


class BLFCRYPTHasher(PasswordHasher):
    """
    BLF-CRYPT password hasher.

    Supports rounds and provides compatibility with dovecot on
    *BSD systems.
    """

    @property
    def scheme(self):
        return "{BLF-CRYPT}" if self._target == "local" else "{CRYPT}"

    def _b64encode(self, pwhash):
        return pwhash

    def _encrypt(self, clearvalue, salt=None):
        # Using the parameter for rounds will generate the error
        # ValueError: rounds too high (bcrypt requires <= 31 rounds)
        # when using the bcrypt hasher.
        # rounds = parameters.get_global_parameter("rounds_number")
        # To get around this, I use the default of 12.
        rounds = 12
        bcrypt.using(rounds=rounds)
        return bcrypt.hash(clearvalue)

    def verify(self, clearvalue, hashed_value):
        return bcrypt.verify(clearvalue, hashed_value)


class MD5CRYPTHasher(PasswordHasher):
    """
    MD5-CRYPT password hasher.

    This scheme can't be considered as secure anymore.
    """
    _weak = True

    @property
    def scheme(self):
        return "{MD5-CRYPT}" if self._target == "local" else "{CRYPT}"

    def _b64encode(self, pwhash):
        return pwhash

    def _encrypt(self, clearvalue, salt=None):
        return md5_crypt.hash(clearvalue)

    def verify(self, clearvalue, hashed_value):
        return md5_crypt.verify(clearvalue, hashed_value)


class SHA256CRYPTHasher(PasswordHasher):
    """
    SHA256-CRYPT password hasher.

    Supports rounds and is a good compromise between security and
    performance.
    """

    @property
    def scheme(self):
        return "{SHA256-CRYPT}" if self._target == "local" else "{CRYPT}"

    def _b64encode(self, pwhash):
        return pwhash

    def _encrypt(self, clearvalue, salt=None):
        rounds = param_tools.get_global_parameter("rounds_number")
        sha256_crypt.using(rounds=rounds)
        return sha256_crypt.hash(clearvalue)

    def verify(self, clearvalue, hashed_value):
        return sha256_crypt.verify(clearvalue, hashed_value)


class SHA512CRYPTHasher(PasswordHasher):
    """
    SHA512-CRYPT password hasher.

    Supports rounds and is the strongest scheme provided by
    Modoboa. Requires more resource than SHA256-CRYPT.
    """

    @property
    def scheme(self):
        return "{SHA512-CRYPT}" if self._target == "local" else "{CRYPT}"

    def _b64encode(self, pwhash):
        return pwhash

    def _encrypt(self, clearvalue, salt=None):
        rounds = param_tools.get_global_parameter("rounds_number")
        sha512_crypt.using(rounds=rounds)
        return sha512_crypt.hash(clearvalue)

    def verify(self, clearvalue, hashed_value):
        return sha512_crypt.verify(clearvalue, hashed_value)
