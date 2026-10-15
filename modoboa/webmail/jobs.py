"""Async (RQ) jobs definition."""

import logging

from django.utils import timezone
from django.utils.translation import gettext as _

import django_rq

from modoboa.webmail import constants, models
from modoboa.webmail.lib import sendmail

logger = logging.getLogger("modoboa.jobs")


def send_scheduled_message(message_id: int):
    message = models.ScheduledMessage.objects.filter(id=message_id).first()
    if message is None:
        # Cancelled while the job was waiting in the queue
        return
    if message.status != constants.SchedulingState.SENDING.value:
        # Flagged as interrupted by send_scheduled_messages: sending it now
        # could duplicate a message the user has already rescheduled.
        return
    try:
        sent = sendmail.send_scheduled_message(message)
    except Exception:
        logger.exception("Failed to send scheduled message %s", message_id)
        message.status = constants.SchedulingState.SEND_ERROR.value
        message.error = _("Unexpected error while sending the message")
        message.save()
        raise
    if sent:
        message.delete()


def send_scheduled_messages():
    now = timezone.now().replace(second=0, microsecond=0)
    # A job lost by the queue (worker crash, Redis flush...) would leave
    # its message in the SENDING state forever: flag it so the user can
    # reschedule it.
    models.ScheduledMessage.objects.filter(
        status=constants.SchedulingState.SENDING.value,
        scheduled_datetime__lte=now - constants.SCHEDULED_SENDING_TIMEOUT,
    ).update(
        status=constants.SchedulingState.SEND_ERROR.value,
        error=_("Sending was interrupted, please reschedule the message"),
    )
    messages = models.ScheduledMessage.objects.filter(
        scheduled_datetime__lte=now,
        status=constants.SchedulingState.SCHEDULED.value,
    )
    queue = django_rq.get_queue("modoboa")
    for message in messages:
        message.status = constants.SchedulingState.SENDING.value
        message.save()
        queue.enqueue(send_scheduled_message, message_id=message.id)
