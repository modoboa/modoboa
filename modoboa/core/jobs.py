"""Async jobs definition."""

import datetime
import logging

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

    message_history_maximum_age = param_tools.get_global_parameter(
        "message_history_maximum_age"
    )
    logger.info(
        f"Deleting messages in history older than {message_history_maximum_age} days..."
    )
    limit = timezone.now() - datetime.timedelta(message_history_maximum_age)
    Maillog.objects.filter(date__lt=limit).delete()
