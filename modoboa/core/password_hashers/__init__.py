# -*- coding: utf-8 -*-

"""
Password hashers for Modoboa.
"""

from __future__ import unicode_literals

import os

from django.utils.encoding import force_text

from modoboa.core.password_hashers.advanced import (  # NOQA:F401
    BLFCRYPTHasher, MD5CRYPTHasher, SHA256CRYPTHasher, SHA512CRYPTHasher
)
from modoboa.core.password_hashers.base import (  # NOQA:F401
    CRYPTHasher, MD5Hasher, PLAINHasher, SHA256Hasher
)
from modoboa.lib.sysutils import exec_cmd


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
    supported_schemes = ["{PLAIN}"]
    dpath = None
    code, output = exec_cmd("which doveadm")
    if not code:
        dpath = force_text(output).strip()
    else:
        known_paths = ("/usr/bin/doveadm", "/usr/local/bin/doveadm")
        for fpath in known_paths:
            if os.path.isfile(fpath) and os.access(fpath, os.X_OK):
                dpath = fpath
    if dpath:
        try:
            code, schemes = exec_cmd("%s pw -l" % dpath)
        except OSError:
            pass
        else:
            supported_schemes = ["{{{}}}".format(scheme)
                                 for scheme in force_text(schemes).split()]

    return supported_schemes
