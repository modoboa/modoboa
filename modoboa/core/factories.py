import factory
from django.contrib.auth.models import Group
from . import models


class GroupFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Group

    name = 'DefaultGroup'


class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.User

    email = factory.LazyAttribute(lambda a: a.username)
    password = '{PLAIN}toto'

    # mailbox = factory.RelatedFactory(
    #     MailboxFactory, 'user',
    #     address=factory.LazyAttribute(
    #         lambda m: m.user.email.replace('@%s' % m.domain.name, '')
    #     )
    # )

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for group in extracted:
                self.groups.add(Group.objects.get(name=group))
