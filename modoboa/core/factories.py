import factory
from django.contrib.auth.models import Group
from . import models


class PermissionFactory(factory.DjangoModelFactory):
    ABSTRACT_FACTORY = True

    @factory.post_generation
    def set_permission(self, create, extracted, **kwargs):
        if not create:
            return
        self.post_create(models.User.objects.get(pk=1))


class GroupFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Group

    name = 'DefaultGroup'


class UserFactory(PermissionFactory):
    FACTORY_FOR = models.User
    FACTORY_DJANGO_GET_OR_CREATE = ("username", )

    email = factory.LazyAttribute(lambda a: a.username)
    password = '{PLAIN}toto'

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for group in extracted:
                self.groups.add(Group.objects.get(name=group))
