"""Factories for core application."""

import factory

from django.contrib.auth.models import Group

from . import models


class PermissionFactory(factory.django.DjangoModelFactory):
    """A base factory to handle permissions."""

    class Meta:
        abstract = True

    @factory.post_generation
    def set_permission(self, create, extracted, **kwargs):
        if not create:
            return
        self.post_create(models.User.objects.filter(is_superuser=True).first())


class GroupFactory(factory.django.DjangoModelFactory):
    """A factory to create Group instances."""

    class Meta:
        model = Group

    name = "DefaultGroup"


class UserFactory(PermissionFactory):
    """A factory to create User instances."""

    class Meta:
        model = models.User
        django_get_or_create = ("username",)

    email = factory.LazyAttribute(lambda a: a.username)
    password = "{PLAIN}toto"

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for group in extracted:
                self.groups.add(Group.objects.get(name=group))


class LogFactory(factory.django.DjangoModelFactory):
    """Factory for Log."""

    class Meta:
        model = models.Log

    logger = "modoboa.admin"
    message = "A message"
    level = "info"


class UserFidoKeyFactory(factory.django.DjangoModelFactory):
    """Factory for UserFidoKey."""

    class Meta:
        model = models.UserFidoKey

    name = factory.Sequence(lambda n: f"Name {n}")
    credential_data = "data"
