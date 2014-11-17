"""
Fixtures factories.
"""
import factory

from modoboa.core.factories import PermissionFactory, UserFactory
from . import models


class DomainFactory(PermissionFactory):
    FACTORY_FOR = models.Domain
    FACTORY_DJANGO_GET_OR_CREATE = ("name", )

    quota = 10
    enabled = True


class MailboxFactory(PermissionFactory):
    FACTORY_FOR = models.Mailbox

    domain = factory.SubFactory(DomainFactory)
    user = factory.SubFactory(UserFactory)
    quota = 10
    enabled = True


class AliasFactory(PermissionFactory):
    FACTORY_FOR = models.Alias

    enabled = True


def populate_database():
    """Create test data.

    2 domains, 1 domain admin, 2 users
    """
    dom = DomainFactory.create(name="test.com")
    admin = UserFactory(
        username="admin@test.com", groups=('DomainAdmins', ), password='{PLAIN}toto'
    )
    MailboxFactory(address='admin', domain=dom, user=admin)
    account = UserFactory.create(
        username="user@test.com", groups=('SimpleUsers',),
    )
    MailboxFactory.create(address='user', domain=dom, user=account)

    fwd = AliasFactory.create(
        address='forward', domain=dom, extmboxes='user@external.com'
    )
    al = AliasFactory.create(
        address='alias', domain=dom
    )
    al.mboxes.add(account.mailbox_set.all()[0])
    AliasFactory.create(
        address='postmaster', domain=dom, extmboxes='toto@titi.com,test@truc.fr'
    )
    dom.add_admin(admin)

    dom2 = DomainFactory.create(name='test2.com', quota=0)
    admin = UserFactory.create(
        username='admin@test2.com', groups=('DomainAdmins',), password='{PLAIN}toto'
    )
    MailboxFactory.create(address='admin', domain=dom2, user=admin)
    u = UserFactory.create(
        username='user@test2.com', groups=('SimpleUsers',)
    )
    MailboxFactory.create(address='user', domain=dom2, user=u)
    dom2.add_admin(admin)
