"""Postfix auto reply factories."""

import factory

from modoboa.admin import factories as admin_factories
from . import models


class ARmessageFactory(factory.django.DjangoModelFactory):
    """Factory to create ARmessage."""

    class Meta:
        model = models.ARmessage
        django_get_or_create = ("mbox",)

    mbox = factory.SubFactory(admin_factories.MailboxFactory)
    subject = "I'm absent"
    content = "I'll write you back ASAP"
    enabled = True
