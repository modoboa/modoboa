"""
Password hashers for Modoboa.
"""

from django.utils.encoding import smart_text

from modoboa.core.password_hashers.advanced import (  # NOQA:F401
    BLFCRYPTHasher, MD5CRYPTHasher, SHA256CRYPTHasher, SHA512CRYPTHasher,
    ARGON2IDHasher
)
from modoboa.core.password_hashers.base import (  # NOQA:F401
    CRYPTHasher, MD5Hasher, PLAINHasher, SHA256Hasher
)
from modoboa.lib.sysutils import doveadm_cmd


def get_password_hasher(scheme):
    """Retrieve the hasher corresponding to :keyword:`scheme`.

    If no class is found, `PLAINHasher` is returned.

    :param str scheme: a valid scheme name
    :rtype: PasswordHasher sub class
    :return: The hasher class
    """
    try:
        scheme = scheme.replace("-", "")
        hasher = globals()["%sHasher" % scheme.upper()]
    except KeyError:
        hasher = PLAINHasher
    return hasher


def get_dovecot_schemes():
    """Return schemes supported by dovecot"""
    supported_schemes = None
    try:
        _, schemes = doveadm_cmd("pw -l")
    except OSError:
        pass
    else:
        supported_schemes = ["{{{}}}".format(smart_text(scheme))
                             for scheme in schemes.split()]

    if not supported_schemes:
        supported_schemes = ['{PLAIN}']

    return supported_schemes
