from datetime import timedelta, datetime

from modoboa.core import models
from modoboa.core.password_hashers import cache_available_passowrd_hasher


def job_retrieve_available_hashers(bypass_condition=False):
    localconfig = models.LocalConfig.objects.first()
    cache = localconfig.cache
    password_scheme_last_mod = cache.get_last_mod(
        "password_scheme_choice", "core", False)
    cur_dt = datetime.utcnow()
    condition = (bypass_condition or
                 password_scheme_last_mod is None or
                 password_scheme_last_mod < cur_dt - timedelta(weeks=4)
                 )
    if condition:
        cache_available_passowrd_hasher()

