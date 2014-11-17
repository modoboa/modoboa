import factory
from modoboa.core.factories import PermissionFactory
from . import models


class ServiceFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Service
    FACTORY_DJANGO_GET_OR_CREATE = ('name', )

    name = 'dummy'


class RelayDomainFactory(PermissionFactory):
    FACTORY_FOR = models.RelayDomain

    target_host = 'external.host.tld'
    enabled = True
    verify_recipients = True
    service = factory.SubFactory(ServiceFactory)


class RelayDomainAliasFactory(PermissionFactory):
    FACTORY_FOR = models.RelayDomainAlias

    enabled = True
