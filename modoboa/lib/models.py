import reversion
from django.db import models
from django.conf import settings


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


class Log(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=255)
    level = models.CharField(max_length=15)
    logger = models.CharField(max_length=30)
