"""Transport factories."""

import factory

from modoboa.core.factories import PermissionFactory

from . import models


class TransportFactory(PermissionFactory):
    """Factory for Transport."""

    class Meta:
        model = models.Transport
        django_get_or_create = ("pattern", )

    pattern = factory.Sequence(lambda n: "transport{}".format(n))
    service = "relay"
    next_hop = "[external.host.tld]:25"

