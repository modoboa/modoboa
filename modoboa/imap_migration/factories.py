"""IMAP migration factories."""

import factory

from modoboa.admin import factories as admin_factories

from . import models


class EmailProviderFactory(factory.django.DjangoModelFactory):
    """Factory for EmailProvider."""

    class Meta:
        model = models.EmailProvider

    name = factory.Sequence(lambda n: f"Provider {n}")
    address = "127.0.0.1"
    port = 143


class EmailProviderDomainFactory(factory.django.DjangoModelFactory):
    """Factory for EmailProviderDomain."""

    class Meta:
        model = models.EmailProviderDomain

    provider = factory.SubFactory(EmailProviderFactory)


class MigrationFactory(factory.django.DjangoModelFactory):
    """Factory for Migration."""

    class Meta:
        model = models.Migration

    mailbox = factory.SubFactory(admin_factories.MailboxFactory)
    provider = factory.SubFactory(EmailProviderFactory)
