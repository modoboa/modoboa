from django.db import models
from django.conf import settings


class Parameter(models.Model):
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    @property
    def shortname(self):
        return self.name.split(".")[1].lower()


class UserParameter(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    @property
    def shortname(self):
        return self.name.split(".")[1].lower()
