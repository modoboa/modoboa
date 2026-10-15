"""Deployment checks."""

import os

from django.core.checks import Warning, register
from django.utils.translation import gettext as _

import django_rq
from redis.exceptions import RedisError
from rq.cron import CronScheduler

from modoboa.webmail.lib import attachments

CLEANUP_JOB = "modoboa.webmail.lib.attachments.cleanup_orphan_attachments"

W001 = Warning(
    _(
        "The webmail attachments cleanup job is not registered: unused "
        "attachment files will never be removed."
    ),
    hint=_(
        "Add the cleanup_orphan_attachments job to your cron_config.py file "
        "(see the upgrade instructions), then restart the RQ cron scheduler."
    ),
    id="modoboa.webmail.W001",
)

W002 = Warning(
    _(
        "The legacy webmail attachments directory still exists inside "
        "MEDIA_ROOT, which may be served by the web server."
    ),
    hint=_("Run the purge_webmail_legacy_data management command."),
    id="modoboa.webmail.W002",
)


@register(deploy=True)
def check_cleanup_job_is_registered(app_configs, **kwargs):
    """Ensure the running cron schedulers know the cleanup job.

    Existing installations keep their own cron_config.py file, which
    does not contain jobs added by newer versions.
    """
    try:
        schedulers = CronScheduler.all(django_rq.get_connection("modoboa"))
    except RedisError:
        return []
    if not schedulers:
        # No scheduler running: nothing to compare with
        return []
    for scheduler in schedulers:
        if any(job.func_name == CLEANUP_JOB for job in scheduler.get_jobs()):
            return []
    return [W001]


@register(deploy=True)
def check_legacy_attachments_dir(app_configs, **kwargs):
    """Ensure the attachments of previous versions have been purged."""
    if os.path.isdir(attachments.get_legacy_attachments_dir()):
        return [W002]
    return []
