from rq import get_current_job

from modoboa.core.password_hashers import cache_available_passowrd_hasher


def job_retrieve_available_hashers():
    if get_current_job() is None:
        return
    cache_available_passowrd_hasher()
