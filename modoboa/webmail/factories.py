"""Webmail factories."""

import factory

from modoboa.admin import factories as admin_factories

from modoboa.webmail import models


class ScheduledMessageFactory(factory.django.DjangoModelFactory):
    """Scheduled message factory."""

    class Meta:
        model = models.ScheduledMessage

    account = factory.SubFactory(admin_factories.UserFactory)
    sender = "sender@test.com"
    subject = "Scheduled Message"
    to = "recipient@domain.test"
