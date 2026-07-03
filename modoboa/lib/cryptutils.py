"""Crypto related utilities."""

import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils.encoding import smart_bytes, smart_str


def random_key(length=16):
    """Generate a new key used to encrypt user passwords in session storage."""
    chars = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
    return get_random_string(length, chars)


def random_hex_key(length=16):
    """Generate a new hexadecimal key."""
    chars = "abcdefABCDEF0123456789"
    return get_random_string(length, chars)


def _master_secret() -> bytes:
    """Return the secret used to derive encryption keys.

    A dedicated high-entropy key can be provided through the
    ``MODOBOA_ENCRYPTION_KEY`` setting, which decouples stored-data
    encryption from ``SECRET_KEY`` (sessions, cookies...). When unset,
    the full ``SECRET_KEY`` is used.
    """
    secret = getattr(settings, "MODOBOA_ENCRYPTION_KEY", "") or settings.SECRET_KEY
    return smart_bytes(secret)


def derive_key(purpose: str) -> bytes:
    """Derive a 32-byte key dedicated to ``purpose`` using HKDF-SHA256.

    Deriving a subkey per purpose ensures that a component never
    decrypts data belonging to another one and that the master secret
    is never used directly as an encryption key.
    """
    kdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"modoboa.cryptutils." + smart_bytes(purpose),
    )
    return kdf.derive(_master_secret())


def get_fernet(purpose: str) -> Fernet:
    """Return a Fernet instance keyed for the given purpose."""
    return Fernet(base64.urlsafe_b64encode(derive_key(purpose)))


def _get_legacy_fernet() -> Fernet:
    """Return a Fernet instance using the historical key derivation.

    Old data was encrypted with a key taken directly from
    ``SECRET_KEY[:32]``: only kept to decrypt it.
    """
    secret_key = base64.urlsafe_b64encode(smart_bytes(settings.SECRET_KEY[:32]))
    return Fernet(secret_key)


def encrypt(clear_value, purpose: str = "generic") -> str:
    """Encrypt a value using a key derived for ``purpose``."""
    return smart_str(get_fernet(purpose).encrypt(smart_bytes(clear_value)))


def decrypt(encrypted_value, purpose: str = "generic") -> str:
    """Decrypt a value, falling back to the legacy key for old data."""
    token = smart_bytes(encrypted_value)
    try:
        return smart_str(get_fernet(purpose).decrypt(token))
    except InvalidToken:
        return smart_str(_get_legacy_fernet().decrypt(token))


def get_password(request):
    """
    Retrieve and decrypt the users password from session storage.

    This is used by modoboa-webmail to allow the user to send/receive e-mails
    without having to ask the user for a password on each connection to the
    postfix/dovecot server.
    """
    try:
        return decrypt(request.session["password"], purpose="session")
    except KeyError:
        return None
    except InvalidToken:
        # Data encrypted before a key change: force re-authentication.
        return None
