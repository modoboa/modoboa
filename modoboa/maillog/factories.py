"""App. factories."""

import factory

from django.utils import timezone

from modoboa.admin import factories as admin_factories

from . import models


class MaillogFactory(factory.DjangoModelFactory):
    """Factory class for Maillog."""

    class Meta:
        model = models.Maillog

    queue_id = factory.Sequence(lambda n: "ID{}".format(n))
    date = timezone.now()
    sender = factory.Sequence(lambda n: "sender{}@example.test".format(n))
    rcpt = factory.Sequence(lambda n: "rcpt{}@example2.test".format(n))
    size = 100
    status = "sent"
    from_domain = factory.SubFactory(admin_factories.DomainFactory)
    to_domain = factory.SubFactory(admin_factories.DomainFactory)
