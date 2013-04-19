from django.db import models
from django.contrib.auth.models import User


class Parameter(models.Model):
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    @property
    def shortname(self):
        return self.name.split(".")[1].lower()


class UserParameter(models.Model):
    user = models.ForeignKey("auth.User")
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    @property
    def shortname(self):
        return self.name.split(".")[1].lower()
