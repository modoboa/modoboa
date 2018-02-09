# -*- coding: utf-8 -*-

"""
Fixtures factories.
"""

from __future__ import unicode_literals

import factory

from modoboa.core.factories import PermissionFactory, UserFactory
from . import models


class DomainFactory(PermissionFactory):

    """Factory to create Domains."""

    class Meta:
        model = models.Domain
        django_get_or_create = ("name", )

    type = "domain"  # NOQA:A003
    quota = 0
    default_mailbox_quota = 10
    enabled = True


class DomainAliasFactory(PermissionFactory):

    """Factory to create DomainAlias objects."""

    class Meta:
        model = models.DomainAlias
        django_get_or_create = ("name", )

    target = factory.SubFactory(DomainFactory)
    enabled = True


class MailboxFactory(PermissionFactory):

    """A factory to create Mailbox instances."""

    class Meta:
        model = models.Mailbox
        django_get_or_create = ("address", "domain")

    domain = factory.SubFactory(DomainFactory)
    user = factory.SubFactory(UserFactory)
    quota = 10


class AliasRecipientFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.AliasRecipient


class AliasFactory(PermissionFactory):

    class Meta:
        model = models.Alias

    enabled = True


class SenderAddressFactory(factory.django.DjangoModelFactory):
    """Factory for SenderAddress model."""

    mailbox = factory.SubFactory(MailboxFactory)

    class Meta:
        model = models.SenderAddress


def populate_database():
    """Create test data.

    2 domains, 1 domain admin, 2 users
    """
    dom = DomainFactory(name="test.com", quota=50)
    admin = UserFactory(
        username="admin@test.com", groups=("DomainAdmins", ),
        password="{PLAIN}toto"
    )
    MailboxFactory(address="admin", domain=dom, user=admin)
    account = UserFactory.create(
        username="user@test.com", groups=("SimpleUsers",),
    )
    MailboxFactory.create(address="user", domain=dom, user=account)

    al = AliasFactory.create(
        address="forward@test.com", domain=dom
    )
    AliasRecipientFactory.create(
        address="user@external.com", alias=al)

    al = AliasFactory.create(
        address="alias@test.com", domain=dom
    )
    mb = account.mailbox
    AliasRecipientFactory.create(
        address=mb.full_address, alias=al, r_mailbox=mb)

    al = AliasFactory.create(
        address="postmaster@test.com", domain=dom
    )
    for address in ["toto@titi.com", "test@truc.fr"]:
        AliasRecipientFactory.create(address=address, alias=al)

    dom.add_admin(admin)

    dom2 = DomainFactory.create(name="test2.com", default_mailbox_quota=0)
    admin = UserFactory.create(
        username="admin@test2.com", groups=("DomainAdmins",),
        password="{PLAIN}toto"
    )
    MailboxFactory.create(address="admin", domain=dom2, user=admin)
    u = UserFactory.create(
        username="user@test2.com", groups=("SimpleUsers",)
    )
    MailboxFactory.create(address="user", domain=dom2, user=u)
    dom2.add_admin(admin)
