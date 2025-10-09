"""
Base password hashers.

Contains weak hashers (the original ones) available with Modoboa.
"""

import base64

import hashlib
from random import Random
import string
from typing import Optional

from django.utils.crypto import constant_time_compare
from django.utils.encoding import force_bytes, force_str


class MetaHasher(type):
    """
    PasswordHasher Metaclass
    Allow classmethod to be properties
    """

    @property
    def name(cls):
        """Returns the name of the hasher"""
        return cls.__name__.rstrip("Hasher").lower()

    @property
    def label(cls):
        """Returns the label of the hasher"""
        result = cls.name
        tags = []
        if cls._weak:
            tags.append("weak")
        if cls.deprecated:
            tags.append("deprecated")
        if tags:
            result += f" ({', '.join(tags)})"
        return result


class PasswordHasher(metaclass=MetaHasher):
    """
    Base class of all hashers.
    """

    _weak: bool = False
    deprecated: bool = False
    scheme: str

    def __init__(self, target="local"):
        self._target = target

    def _encrypt(self, clearvalue: str, salt: Optional[str] = None) -> str:
        raise NotImplementedError

    def _b64encode(self, pwhash):
        """Encode :keyword:`pwhash` using base64 if needed.

        :param str pwhash: password hash
        :return: base64 encoded hash or original hash
        """
        if self._target == "ldap":
            return base64.b64encode(pwhash)
        return pwhash

    def encrypt(self, clearvalue: str) -> str:
        """Encrypt a password.

        The format used to store passwords is the same than dovecot's one::

          {SCHEME}<hash>

        <hash> may differ according to the used scheme.

        :param str clearvalue: clear password
        :rtype: str
        :return: encrypted password
        """
        pwhash = self._b64encode(self._encrypt(force_str(clearvalue)))
        return f"{self.scheme}{force_str(pwhash)}"

    def verify(self, clearvalue, hashed_value):
        """Verify a password against a hashed value.

        :param str clearvalue: clear password
        :param str hashed_value: password previously hashed
        :return: True if passwords match, False otherwise
        """
        return constant_time_compare(
            self._b64encode(self._encrypt(clearvalue, hashed_value)), hashed_value
        )

    def needs_rehash(self, hashed_value):
        """Check if the provided hash needs rehasing accoring to the current
        parameters

        :param str hashed_value: hased password
        :rtype bool
        :return: True if the password needs rehash, false otherwise
        """
        return False

    @classmethod
    def get_password_hashers(cls) -> list[type["PasswordHasher"]]:
        """Return all the PasswordHasher supported by Modoboa"""
        return [hasher for hasher in cls.__subclasses__()]

    @classmethod
    def get_deprecated_password_hashers(cls) -> list[type["PasswordHasher"]]:
        """Return all the PasswordHasher supported by Modoboa and marked as deprecated."""
        return [hasher for hasher in cls.__subclasses__() if hasher.deprecated]


class PLAINHasher(PasswordHasher):
    """
    Plain (ie. clear) password hasher.
    """

    _weak = True

    @property
    def scheme(self):
        return "{PLAIN}"

    def _encrypt(self, clearvalue, salt=None):
        return clearvalue


class MD5Hasher(PasswordHasher):
    """
    MD5 password hasher.

    Uses python `hashlib` standard module.
    """

    _weak = True

    @property
    def scheme(self):
        return "{MD5}"

    def _encrypt(self, clearvalue, salt=None):
        obj = hashlib.md5(force_bytes(clearvalue))
        return obj.hexdigest()


class SHA256Hasher(PasswordHasher):
    """
    SHA256 password hasher.

    Uses python `hashlib` and `base64` standard modules.
    """

    _weak = True

    @property
    def scheme(self):
        return "{SHA256}"

    def _encrypt(self, clearvalue, salt=None):
        return hashlib.sha256(force_bytes(clearvalue)).digest()

    def _b64encode(self, pwhash):
        """Encode :keyword:`pwhash` using base64.

        :param str pwhash: password hash
        :return: base64 encoded hash
        """
        return base64.b64encode(pwhash)
