"""
Advanced (ie. stronger) password hashers.

This module relies on `passlib` to provide more secure hashers.
"""
from passlib.hash import bcrypt, md5_crypt, sha256_crypt, sha512_crypt
from modoboa.core.password_hashers.base import PasswordHasher
from modoboa.lib import parameters


class BLFCRYPTHasher(PasswordHasher):
    """
    BLF-CRYPT password hasher.

    Supports rounds and provides compatibility with dovecot on
    *BSD systems.
    """
    @property
    def scheme(self):
        return '{BLF-CRYPT}' if self._target == 'local' else '{CRYPT}'

    def _b64encode(self, pwhash):
        return pwhash

    def _encrypt(self, clearvalue, salt=None):
        # Using the parameter for rounds will generate the error
        # ValueError: rounds too high (bcrypt requires <= 31 rounds)
        # when using the bcrypt hasher.
        # rounds = int(parameters.get_admin('ROUNDS_NUMBER'))
        # To get around this, I use the default of 12.
        rounds = 12
        return bcrypt.encrypt(clearvalue, rounds=rounds)

    def verify(self, clearvalue, hashed_value):
        return bcrypt.verify(clearvalue, hashed_value)


class MD5CRYPTHasher(PasswordHasher):

    """
    MD5-CRYPT password hasher.

    This scheme can't be considered as secure anymore.
    """
    @property
    def scheme(self):
        return '{MD5-CRYPT}' if self._target == 'local' else '{CRYPT}'

    def _b64encode(self, pwhash):
        return pwhash

    def _encrypt(self, clearvalue, salt=None):
        return md5_crypt.encrypt(clearvalue)

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
        return '{SHA256-CRYPT}' if self._target == 'local' else '{CRYPT}'

    def _b64encode(self, pwhash):
        return pwhash

    def _encrypt(self, clearvalue, salt=None):
        rounds = int(parameters.get_admin('ROUNDS_NUMBER'))
        return sha256_crypt.encrypt(clearvalue, rounds=rounds)

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
        return '{SHA512-CRYPT}' if self._target == 'local' else '{CRYPT}'

    def _b64encode(self, pwhash):
        return pwhash

    def _encrypt(self, clearvalue, salt=None):
        rounds = int(parameters.get_admin('ROUNDS_NUMBER'))
        return sha512_crypt.encrypt(clearvalue, rounds=rounds)

    def verify(self, clearvalue, hashed_value):
        return sha512_crypt.verify(clearvalue, hashed_value)
