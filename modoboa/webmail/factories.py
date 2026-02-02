"""Webmail factories."""

import factory

from modoboa.admin import factories as admin_factories

from modoboa.webmail import constants, models


class ScheduledMessageFactory(factory.django.DjangoModelFactory):
    """Scheduled message factory."""

    class Meta:
        model = models.ScheduledMessage

    status = constants.SchedulingState.SCHEDULED
    account = factory.SubFactory(admin_factories.UserFactory)
    sender = "sender@test.com"
    subject = "Scheduled Message"
    to = "recipient@domain.test"
