# coding: utf-8

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _, ugettext_noop

reseller_limits_tpl = [
    "domains_limit",
    "domain_aliases_limit",
    "mailboxes_limit",
    "mailbox_aliases_limit",
    ]

class LimitsPool(models.Model):
    user = models.OneToOneField(User)

    def getcurvalue(self, lname):
        l = Limit.objects.get(name=lname)
        return l.curvalue

    def getmaxvalue(self, lname):
        l = Limit.objects.get(name=lname)
        return l.maxvalue

    def inc_curvalue(self, lname, nb=1):
        l = Limit.objects.get(name=lname)
        if l.curvalue + nb > l.maxvalue:
            return False
        l.curvalue += nb
        l.save()
        return True

    def get_limit(self, lname):
        return Limit.objects.get(name=lname)

class Limit(models.Model):
    name = models.CharField(max_length=255)
    curvalue = models.IntegerField(default=0)
    maxvalue = models.IntegerField(default=0)
    pool = models.ForeignKey(LimitsPool)

class ResellerObject(models.Model):
    user = models.ForeignKey(User)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
