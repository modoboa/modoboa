import factory
from modoboa.core.models import User
from modoboa.core.factories import UserFactory
from . import models


class DomainFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Domain

    quota = 10
    enabled = True


class MailboxFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Mailbox

    quota = 0
    use_domain_quota = True


class AliasFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Alias


def populate_database():
    """Create test data.

    2 domains, 1 domain admin, 2 users
    """
    sa = User.objects.get(pk=1)
    dom = DomainFactory.create(name="test.com")
    admin = UserFactory(
        username="admin@test.com", groups=('DomainAdmins',)
    )
    admin.post_create(sa)
    MailboxFactory(address='admin', domain=dom, user=admin)
    account = UserFactory.create(
        username="user@test.com", groups=('SimpleUsers',)
    )
    account.post_create(sa)
    MailboxFactory.create(address='user', domain=dom, user=account)

    dom2 = DomainFactory(name='test2.com')
    u = UserFactory(
        username='user@test2.com', groups=('SimpleUsers',)
    )
    u.post_create(sa)
    MailboxFactory(address='user', domain=dom2, user=u)

    dom.add_admin(admin)
