import factory
from modoboa.core.factories import PermissionFactory
from . import models


class ServiceFactory(factory.DjangoModelFactory):

    """Factory to create Service instances."""

    class Meta:
        model = models.Service
        django_get_or_create = ('name', )

    name = 'dummy'


class RelayDomainFactory(PermissionFactory):

    """Factory to create RelayDomain instances."""

    class Meta:
        model = models.RelayDomain

    target_host = 'external.host.tld'
    enabled = True
    verify_recipients = True
    service = factory.SubFactory(ServiceFactory)


class RelayDomainAliasFactory(PermissionFactory):

    """Factory to create RelayDomainAliases instances."""

    class Meta:
        model = models.RelayDomainAlias

    enabled = True
