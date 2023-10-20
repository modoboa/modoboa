"""
Password hashers for Modoboa.
"""

from django.conf import settings
from django.utils.encoding import smart_str

from modoboa.core.password_hashers.advanced import (  # NOQA:F401
    BLFCRYPTHasher, MD5CRYPTHasher, SHA256CRYPTHasher, SHA512CRYPTHasher,
    ARGON2IDHasher, SSHAHasher
)
from modoboa.core.password_hashers.base import (  # NOQA:F401
    CRYPTHasher, MD5Hasher, PLAINHasher, SHA256Hasher, PasswordHasher
)
from modoboa.core import models

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
    """Return schemes supported by Dovecot.

    It first try to get supported schemes fron the settings, then from the
    doveadm output, and fallback to {MD5-CRYPT} and {PLAIN} if the command
    is not found.

    :return: A list of supported '{SCHEME}'
    """
    schemes = getattr(settings, "DOVECOT_SUPPORTED_SCHEMES", None)
    default_schemes = "MD5-CRYPT PLAIN"

    if not schemes:
        try:
            retcode, schemes = doveadm_cmd("pw -l")
        except OSError:
            schemes = default_schemes
        else:
            if retcode:
                schemes = default_schemes

    return ["{{{}}}".format(smart_str(scheme))
            for scheme in schemes.split()]


def cache_available_passowrd_hasher():
    available_schemes = get_dovecot_schemes()
    password_scheme_choice = [
        (hasher.name, hasher.label)
        for hasher in PasswordHasher.get_password_hashers()
        if hasher().scheme in available_schemes
        ]
    localconfig = models.LocalConfig.objects.first()
    localconfig.cache.set_cache_entry("password_scheme_choice",
                                      password_scheme_choice,
                                      "core")
    localconfig.save(update_fields=["_cache"])
