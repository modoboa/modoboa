# coding: utf-8

"""Models for the limits extensions."""

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _, ugettext_lazy

from modoboa.lib import parameters, events
from modoboa.lib.singleton import Singleton


class LimitTemplates(Singleton):

    def __init__(self):
        self.__templates = [
            ("domain_admins_limit", ugettext_lazy("Domain admins"),
             ugettext_lazy("Maximum number of domain administrators this user "
                           "can create"),
             'Resellers'),
            ("domains_limit", ugettext_lazy("Domains"),
             ugettext_lazy("Maximum number of domains this user can create"),
             'Resellers'),
            ("domain_aliases_limit", ugettext_lazy("Domain aliases"),
             ugettext_lazy(
                 "Maximum number of domain aliases this user can create"),
             'Resellers'),
            ("mailboxes_limit", ugettext_lazy("Mailboxes"),
             ugettext_lazy("Maximum number of mailboxes this user can create")),
            ("mailbox_aliases_limit", ugettext_lazy("Mailbox aliases"),
             ugettext_lazy("Maximum number of mailbox aliases this user "
                           "can create"))
        ]

    @property
    def templates(self):
        return self.__templates + \
            events.raiseQueryEvent('GetExtraLimitTemplates')


class LimitsPool(models.Model):

    user = models.OneToOneField(settings.AUTH_USER_MODEL)

    def create_limits(self, creator):
        """Create limits for this pool.

        All limits defined into ``LimitTemplates`` will be created. If
        the creator is a super administrator, the default maximum values
        will be used.

        :param ``User`` creator: user creating this pool
        """
        for ltpl in LimitTemplates().templates:
            try:
                Limit.objects.get(name=ltpl[0], pool=self)
            except Limit.DoesNotExist:
                maxvalue = (
                    int(parameters.get_admin("DEFLT_%s" % ltpl[0].upper()))
                    if creator.is_superuser else 0
                )
                Limit.objects.create(
                    name=ltpl[0], pool=self, maxvalue=maxvalue
                )

    def getcurvalue(self, lname):
        l = self.limit_set.get(name=lname)
        return l.curvalue

    def getmaxvalue(self, lname):
        l = self.limit_set.get(name=lname)
        return l.maxvalue

    def set_maxvalue(self, lname, value):
        l = self.limit_set.get(name=lname)
        l.maxvalue = value
        l.save()

    def inc_curvalue(self, lname, nb=1):
        l = self.limit_set.get(name=lname)
        l.curvalue += nb
        l.save()

    def dec_curvalue(self, lname, nb=1):
        l = self.limit_set.get(name=lname)
        if not l.curvalue:
            return
        l.curvalue -= nb
        l.save()

    def dec_limit(self, lname, nb=1):
        l = self.limit_set.get(name=lname)
        l.curvalue -= nb
        if l.maxvalue > -1:
            l.maxvalue -= nb
        l.save()

    def inc_limit(self, lname, nb=1):
        l = self.limit_set.get(name=lname)
        l.curvalue += nb
        if l.maxvalue > -1:
            l.maxvalue += nb
        l.save()

    def will_be_reached(self, lname, nb=1):
        l = self.limit_set.get(name=lname)
        if l.maxvalue <= -1:
            return False
        if l.curvalue + nb > l.maxvalue:
            return True
        return False

    def get_limit(self, lname):
        try:
            return self.limit_set.get(name=lname)
        except Limit.DoesNotExist:
            return None


class Limit(models.Model):

    name = models.CharField(max_length=255)
    curvalue = models.IntegerField(default=0)
    maxvalue = models.IntegerField(default=-2)
    pool = models.ForeignKey(LimitsPool)

    class Meta:
        unique_together = (("name", "pool"),)

    @property
    def usage(self):
        if self.maxvalue < 0:
            return -1
        if self.maxvalue == 0:
            return 0
        return int(float(self.curvalue) / self.maxvalue * 100)

    @property
    def label(self):
        for l in LimitTemplates().templates:
            if l[0] == self.name:
                return l[1]
        return ""

    def __str__(self):
        if self.maxvalue == -2:
            return _("undefined")
        if self.maxvalue == -1:
            return _("unlimited")
        if self.maxvalue == 0:
            return "100%"

        return "%d%%" % self.usage
