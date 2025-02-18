"""Password hashers for Modoboa."""

from modoboa.core.password_hashers.advanced import (  # NOQA:F401
    BLFCRYPTHasher,
    MD5CRYPTHasher,
    SHA256CRYPTHasher,
    SHA512CRYPTHasher,
    ARGON2IDHasher,
    SSHAHasher,
)
from modoboa.core.password_hashers.base import (  # NOQA:F401
    CRYPTHasher,
    MD5Hasher,
    PLAINHasher,
    SHA256Hasher,
    PasswordHasher,
)


def get_password_hasher(scheme: str) -> type[PasswordHasher]:
    """Retrieve the hasher corresponding to :keyword:`scheme`.

    If no class is found, `PLAINHasher` is returned.

    :param str scheme: a valid scheme name
    :rtype: PasswordHasher sub class
    :return: The hasher class
    """
    try:
        scheme = scheme.replace("-", "")
        hasher = globals()[f"{scheme.upper()}Hasher"]
    except KeyError:
        hasher = PLAINHasher
    return hasher


def get_configured_password_hasher() -> type[PasswordHasher]:
    """Retrieve the password hasher class currently configured."""
    from modoboa.parameters import tools as param_tools

    scheme = param_tools.get_global_parameter("password_scheme")
    return get_password_hasher(scheme)
