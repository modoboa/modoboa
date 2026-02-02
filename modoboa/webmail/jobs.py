"""Async (RQ) jobs definition."""

from django.utils import timezone

import django_rq

from modoboa.webmail import constants, models
from modoboa.webmail.lib import sendmail


def send_scheduled_message(message_id: int):
    message = models.ScheduledMessage.objects.get(id=message_id)
    if sendmail.send_scheduled_message(message):
        message.delete()


def send_scheduled_messages():
    messages = models.ScheduledMessage.objects.filter(
        scheduled_datetime__lte=timezone.now(),
        status=constants.SchedulingState.SCHEDULED,
    )
    queue = django_rq.get_queue("modoboa")
    for message in messages:
        message.state = constants.SchedulingState.SENDING
        message.save()
        queue.enqueue(send_scheduled_message, message_id=message.id)
