from django.db import models
from django.contrib.auth.models import User

class Parameter(models.Model):
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

class UserParameter(models.Model):
    user = models.ForeignKey("auth.User")
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
