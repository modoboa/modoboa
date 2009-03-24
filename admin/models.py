from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Domain(models.Model):
    name = models.CharField(max_length=100)
    quota = models.IntegerField()
    enabled = models.BooleanField()

class Mailbox(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
#    password = models.CharField(max_length=100)
    quota = models.IntegerField()
#    enabled = models.BooleanField()
    uid = models.IntegerField()
    gid = models.IntegerField()
    path = models.CharField(max_length=200)
    domain = models.ForeignKey(Domain)
    user = models.ForeignKey(User)

    def __str__(self):
        return "%s" % (self.address)


class Alias(models.Model):
    address = models.CharField(max_length=100)
    mbox = models.ForeignKey(Mailbox)
    enabled = models.BooleanField()
