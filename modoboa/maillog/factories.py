"""App. factories."""

import factory

from django.utils import timezone

from modoboa.admin import factories as admin_factories

from . import models


class MaillogFactory(factory.django.DjangoModelFactory):
    """Factory class for Maillog."""

    class Meta:
        model = models.Maillog

    queue_id = factory.Sequence(lambda n: f"ID{n}")
    date = timezone.now()
    sender = factory.Sequence(lambda n: f"sender{n}@example.test")
    rcpt = factory.Sequence(lambda n: f"rcpt{n}@example2.test")
    size = 100
    status = "sent"
    from_domain = factory.SubFactory(admin_factories.DomainFactory)
    to_domain = factory.SubFactory(admin_factories.DomainFactory)
