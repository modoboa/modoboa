"""Modoboa Lib models."""

from django.db import models
from django.conf import settings

from reversion import revisions as reversion


class Parameter(models.Model):
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    @property
    def shortname(self):
        return self.name.split(".")[1].lower()

    def __unicode__(self):
        return self.name

reversion.register(Parameter)


class UserParameter(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    @property
    def shortname(self):
        return self.name.split(".")[1].lower()
