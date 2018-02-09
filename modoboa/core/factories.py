# -*- coding: utf-8 -*-

"""Factories for core application."""

from __future__ import unicode_literals

import factory

from django.contrib.auth.models import Group

from . import models


class PermissionFactory(factory.DjangoModelFactory):

    """A base factory to handle permissions."""

    class Meta(object):
        abstract = True

    @factory.post_generation
    def set_permission(self, create, extracted, **kwargs):
        if not create:
            return
        self.post_create(models.User.objects.filter(is_superuser=True).first())


class GroupFactory(factory.DjangoModelFactory):

    """A factory to create Group instances."""

    class Meta(object):
        model = Group

    name = "DefaultGroup"


class UserFactory(PermissionFactory):

    """A factory to create User instances."""

    class Meta(object):
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


class LogFactory(factory.DjangoModelFactory):
    """Factory for Log."""

    class Meta(object):
        model = models.Log

    logger = "modoboa.admin"
    message = "A message"
    level = "info"
