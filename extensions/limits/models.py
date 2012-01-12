# coding: utf-8

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _, ugettext_noop

class LimitsPool(models.Model):
    user = models.OneToOneField(User)

    maxdomains = models.IntegerField(ugettext_noop("Max domains"),
        default=0,
        help_text=ugettext_noop("Maximum number of domains that can be created by this user"))
    maxdomaliases = models.IntegerField(ugettext_noop("Max domain aliases"),
        default=0,
        help_text=ugettext_noop("Maximum number of domain aliases that can be created by this user"))
    maxmboxes = models.IntegerField(ugettext_noop("Max mailboxes"),
        default=0,
        help_text=ugettext_noop("Maximum number of mailboxes that can be created by this user"))
    maxmbaliases = models.IntegerField(ugettext_noop("Max mailbox aliases"),
        default=0,
        help_text=ugettext_noop("Maximum number of mailbox aliases that can be created by this user"))
