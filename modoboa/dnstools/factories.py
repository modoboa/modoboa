"""App related factories."""

import factory

from modoboa.admin import factories as admin_factories

from . import models


class DNSRecordFactory(factory.django.DjangoModelFactory):
    """Factory for dns records."""

    class Meta:
        model = models.DNSRecord

    domain = factory.SubFactory(admin_factories.DomainFactory)
