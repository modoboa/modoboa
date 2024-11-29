"""Utility functions."""

import environ
import os
from pkg_resources import parse_version
from typing import Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from django.utils.translation import gettext as _

from modoboa.core.extensions import exts_pool
from modoboa.core.password_hashers import get_configured_password_hasher, PasswordHasher
from modoboa.lib.api_client import ModoAPIClient


def parse_map_file(path):
    """Parse a postfix map file and return values."""
    content = {}
    with open(path) as fp:
        for line in fp:
            if not line or line.startswith("#"):
                continue
            name, value = line.split("=", 1)
            content[name.strip()] = value.strip()
    return content


def check_for_updates():
    """Check if a new version of Modoboa is available."""
    from . import models

    local_config = models.LocalConfig.objects.first()
    client = ModoAPIClient()
    extensions = exts_pool.list_all()
    extensions = [
        {
            "label": "Modoboa",
            "name": "modoboa",
            "description": _("The core part of Modoboa"),
            "version": client.local_core_version,
        }
    ] + extensions
    update_avail = False
    for extension in extensions:
        pkgname = extension["name"].replace("_", "-")
        for api_extension in local_config.api_versions:
            if api_extension["name"] != pkgname:
                continue
            extension["last_version"] = api_extension["version"]
            if parse_version(api_extension["version"]) > parse_version(
                extension["version"]
            ):
                extension["update"] = True
                extension["changelog_url"] = api_extension["url"]
                update_avail = True
                break
    return update_avail, extensions


def generate_rsa_private_key(storage_path: str) -> bool:
    """Generate RSA private key for OIDC support.

    :return: False if the key was not generated
    and True if it was."""

    env_path = os.path.join(storage_path, ".env")

    env = environ.Env(OIDC_RSA_PRIVATE_KEY=(str, "NONE"))
    environ.Env.read_env(env_path)

    if env("OIDC_RSA_PRIVATE_KEY") != "NONE":
        return False

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
    )
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    content = bytes(pem)
    content = content.replace(b"\n", b"\\n")
    with open(env_path, "wb") as fp:
        fp.write(b'OIDC_RSA_PRIVATE_KEY="' + content + b'"\n')
    return True


def check_for_deprecated_password_schemes() -> Optional[type[PasswordHasher]]:
    """Check if deprecated password scheme is still in use."""
    from modoboa.core import models

    hasher = get_configured_password_hasher()
    if hasher.deprecated:
        return hasher
    deprecated_hashers = PasswordHasher.get_deprecated_password_hashers()
    for dhasher in deprecated_hashers:
        if models.User.objects.is_password_scheme_in_use(dhasher):
            return dhasher
    return None
