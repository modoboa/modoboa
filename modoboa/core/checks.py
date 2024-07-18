from django.core.checks import register, Info
from django.conf import settings

from modoboa.core.utils import generate_rsa_private_key


@register(deploy=True)
def generate_rsa_private_key_check(app_configs, **kwargs):
    if generate_rsa_private_key(settings.BASE_DIR):
        return Info("Generated the RSA key for OIDC.")
