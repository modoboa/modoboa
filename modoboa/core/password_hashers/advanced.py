"""
Advanced (ie. stronger) password hashers.

This module relies on `passlib` to provide more secure hashers.
"""

from passlib.hash import bcrypt, md5_crypt, sha256_crypt, sha512_crypt

try:
    from argon2 import PasswordHasher as argon2_hasher
    from argon2 import exceptions as argon2_exceptions
except ImportError:
    argon2_hasher = None

from django.conf import settings

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
        return bcrypt.hash(clearvalue, rounds=rounds)

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
        return sha256_crypt.hash(clearvalue, rounds=rounds)

    def verify(self, clearvalue, hashed_value):
        return sha256_crypt.verify(clearvalue, hashed_value)


class SHA512CRYPTHasher(PasswordHasher):
    """
    SHA512-CRYPT password hasher.

    Supports rounds. Requires more resource than SHA256-CRYPT.
    """

    @property
    def scheme(self):
        return "{SHA512-CRYPT}" if self._target == "local" else "{CRYPT}"

    def _b64encode(self, pwhash):
        return pwhash

    def _encrypt(self, clearvalue, salt=None):
        rounds = param_tools.get_global_parameter("rounds_number")
        return sha512_crypt.hash(clearvalue, rounds=rounds)

    def verify(self, clearvalue, hashed_value):
        return sha512_crypt.verify(clearvalue, hashed_value)


if argon2_hasher is not None:
    class ARGON2IDHasher(PasswordHasher):
        """
        argon2 password hasher.

        Supports rounds, memory and number of threads. To be set in settings.py.
        It is the strongest scheme provided by modoboa
        but can only be used with dovecot >= 2.3 and libsodium >= 1.0.13
        """

        def __init__(self,):
            super(ARGON2IDHasher, self).__init__()

            parameters = dict()

            if hasattr(settings, "MODOBOA_ARGON2_TIME_COST"):
                parameters["time_cost"] = settings.MODOBOA_ARGON2_TIME_COST

            if hasattr(settings, "MODOBOA_ARGON2_MEMORY_COST"):
                parameters["memory_cost"] = settings.MODOBOA_ARGON2_MEMORY_COST

            if hasattr(settings, "MODOBOA_ARGON2_PARALLELISM"):
                parameters["parallelism"] = settings.MODOBOA_ARGON2_PARALLELISM

            self.hasher = argon2_hasher(**parameters)

        @property
        def scheme(self):
            return "{ARGON2ID}" if self._target == "local" else "{CRYPT}"

        def _b64encode(self, pwhash):
            return pwhash

        def _encrypt(self, clearvalue, salt=None):
            return self.hasher.hash(clearvalue)

        def verify(self, clearvalue, hashed_value):
            try:
                return self.hasher.verify(hashed_value, clearvalue)
            except argon2_exceptions.VerifyMismatchError:
                return False

        def needs_rehash(self, hashed_value):
            return self.hasher.check_needs_rehash(
                hashed_value.strip(self.scheme)
            )
else:
    class ARGON2IDHasher:
        pass
