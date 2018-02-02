# -*- coding: utf-8 -*-

"""
Password hashers for Modoboa.
"""

from __future__ import unicode_literals

from modoboa.core.password_hashers.advanced import (  # NOQA:F401
    BLFCRYPTHasher, MD5CRYPTHasher, SHA256CRYPTHasher, SHA512CRYPTHasher
)
from modoboa.core.password_hashers.base import (  # NOQA:F401
    CRYPTHasher, MD5Hasher, PLAINHasher, SHA256Hasher
)


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
