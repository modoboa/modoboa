"""
Fixtures factories.
"""
import factory

from modoboa.extensions.admin.factories import (
    DomainFactory, MailboxFactory
)

from . import models


class UserCalendarFactory(factory.DjangoModelFactory):

    class Meta:
        model = models.UserCalendar

    name = factory.Sequence(lambda n: 'User calendar %s' % n)
    mailbox = factory.SubFactory(MailboxFactory)


class SharedCalendarFactory(factory.DjangoModelFactory):

    class Meta:
        model = models.SharedCalendar

    name = factory.Sequence(lambda n: 'Shared calendar %s' % n)
    domain = factory.SubFactory(DomainFactory)


class AccessRuleFactory(factory.DjangoModelFactory):

    class Meta:
        model = models.AccessRule

    mailbox = factory.SubFactory(MailboxFactory)
    calendar = factory.SubFactory(UserCalendarFactory)
