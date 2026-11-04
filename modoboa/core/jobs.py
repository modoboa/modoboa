"""Async jobs definition."""

import datetime
import logging

from django.core.management import call_command

from modoboa.core.models import Log
from modoboa.maillog.models import Maillog
from modoboa.parameters import tools as param_tools

from django.utils import timezone

logger = logging.getLogger("modoboa.jobs")


def clean_logs():
    log_maximum_age = param_tools.get_global_parameter("log_maximum_age")
    logger.info(f"Deleting logs older than {log_maximum_age} days...")
    limit = timezone.now() - datetime.timedelta(log_maximum_age)
    Log.objects.filter(date_created__lt=limit).delete()
    # keep=1: audit handlers need the last version to tell "added" from
    # "modified" and to name deleted objects.
    call_command("deleterevisions", days=log_maximum_age, keep=1, verbosity=0)

    message_history_maximum_age = param_tools.get_global_parameter(
        "message_history_maximum_age"
    )
    logger.info(
        f"Deleting messages in history older than {message_history_maximum_age} days..."
    )
    limit = timezone.now() - datetime.timedelta(message_history_maximum_age)
    Maillog.objects.filter(date__lt=limit).delete()


def communicate_with_public_api(*args, **options):
    call_command("communicate_with_public_api", *args, **options)
