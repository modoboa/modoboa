"""Factories for core application."""

import factory

from django.contrib.auth.models import Group

from . import models


class PermissionFactory(factory.DjangoModelFactory):

    """A base factory to handle permissions."""

    class Meta:
        abstract = True

    @factory.post_generation
    def set_permission(self, create, extracted, **kwargs):
        if not create:
            return
        self.post_create(models.User.objects.filter(is_superuser=True).first())


class GroupFactory(factory.DjangoModelFactory):

    """A factory to create Group instances."""

    class Meta:
        model = Group

    name = "DefaultGroup"


class UserFactory(PermissionFactory):

    """A factory to create User instances."""

    class Meta:
        model = models.User
        django_get_or_create = ("username", )

    email = factory.LazyAttribute(lambda a: a.username)
    password = "{PLAIN}toto"

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for group in extracted:
                self.groups.add(Group.objects.get(name=group))
