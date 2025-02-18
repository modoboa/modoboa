""" Utils for password schemes caching/retrieval. """

from django.conf import settings
from django.core.cache import cache
from django.utils.encoding import smart_str

from modoboa.admin.models.alarm import Alarm
from modoboa.admin.constants import ALARM_CLOSED, ALARM_OPENED

from modoboa.core.constants import DOVEADM_PASS_SCHEME_ALARM

from modoboa.lib.sysutils import doveadm_cmd

from .base import PasswordHasher


def get_dovecot_schemes():
    """Return schemes supported by Dovecot.

    It first try to get supported schemes fron the settings, then from the
    doveadm output, and fallback to {MD5-CRYPT} and {PLAIN} if the command
    is not found.

    :return: A tuple with [0] : a list of supported '{SCHEME}'
    [1] : the status (0=actual schemes, 1=settings schemes, 2=default schemes)
    """
    schemes = getattr(settings, "DOVECOT_SUPPORTED_SCHEMES", None)
    default_schemes = "MD5-CRYPT PLAIN"
    status = 1

    if not schemes:
        try:
            retcode, schemes = doveadm_cmd("pw -l")
        except OSError:
            schemes = default_schemes
            status = 2
        else:
            if retcode:
                schemes = default_schemes
                status = 2
            else:
                status = 0

    # Manage alarms if needed
    doveadm_alarms = Alarm.objects.filter(internal_name=DOVEADM_PASS_SCHEME_ALARM)
    doveadm_alarm = doveadm_alarms.first()
    if status == 0:
        condition = doveadm_alarm is not None and doveadm_alarm.status == ALARM_OPENED
        if condition:
            doveadm_alarm.close()
    elif status == 2:
        if doveadm_alarm is not None:
            if doveadm_alarm.status == ALARM_CLOSED:
                doveadm_alarm.reopen()
        else:
            Alarm.objects.create(
                title="Failed to retrieve available dovecot schemes",
                internal_name=DOVEADM_PASS_SCHEME_ALARM,
            )

    return [f"{{{smart_str(scheme)}}}" for scheme in schemes.split()], status


def cache_available_password_hasher(bypass_cache=False):
    available_schemes, status = get_dovecot_schemes()
    password_scheme_choice = [
        (hasher.name, hasher.label)
        for hasher in PasswordHasher.get_password_hashers()
        if hasher().scheme in available_schemes
    ]
    if status == 0 and not bypass_cache:
        cache.set("password_scheme_choice", password_scheme_choice, 2592000)
    return password_scheme_choice
