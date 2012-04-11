# coding: utf-8

from django import forms
from django.utils.translation import ugettext_noop as _
from django.contrib.auth.models import User, Group
from models import *
from lib import *

class ResourcePoolForm(forms.Form):
    domain_admins_limit = forms.IntegerField(
        ugettext_noop("Max domain admins"),
        help_text=ugettext_noop("Maximum number of domain administrators that can be created by this user")
        )
    domains_limit = forms.IntegerField(ugettext_noop("Max domains"),
        help_text=ugettext_noop("Maximum number of domains that can be created by this user"))
    domain_aliases_limit = forms.IntegerField(ugettext_noop("Max domain aliases"),
        help_text=ugettext_noop("Maximum number of domain aliases that can be created by this user"))
    mailboxes_limit = forms.IntegerField(ugettext_noop("Max mailboxes"),
        help_text=ugettext_noop("Maximum number of mailboxes that can be created by this user"))
    mailbox_aliases_limit = forms.IntegerField(ugettext_noop("Max mailbox aliases"),
        help_text=ugettext_noop("Maximum number of mailbox aliases that can be created by this user"))

    def __init__(self, *args, **kwargs):
        if kwargs.has_key("instance"):
            self.account = kwargs["instance"]
            del kwargs["instance"]
        super(ResourcePoolForm, self).__init__(*args, **kwargs)
        if hasattr(self, "account"):
            if self.account.group != "Resellers":
                del self.fields["domain_admins_limit"]
                del self.fields["domains_limit"]
            self.load_from_user(self.account)

    def check_limit_value(self, lname):
        if self.cleaned_data[lname] < -1:
            raise forms.ValidationError(_("Invalid limit"))
        return self.cleaned_data[lname]

    def clean_domains_limit(self):
        return self.check_limit_value("domains_limit")

    def clean_domain_aliases_limit(self):
        return self.check_limit_value("domain_aliases_limit")

    def clean_mailboxes_limit(self):
        return self.check_limit_value("mailboxes_limit")

    def clean_mailbox_aliases_limit(self):
        return self.check_limit_value("mailbox_aliases_limit")

    def load_from_user(self, user):
        for l in limits_tpl:
            if not self.fields.has_key(l[0]):
                continue
            self.fields[l[0]].initial = user.limitspool.getmaxvalue(l[0])

    def allocate_from_pool(self, limit, pool):
        ol = pool.get_limit(limit.name)
        if ol.maxvalue == -2:
            raise BadLimitValue(_("Your pool is not initialized yet"))
        newvalue = self.cleaned_data[limit.name]
        if newvalue == -1 and ol.maxvalue != -1:
            raise BadLimitValue(_("You're not allowed to define unlimited values"))

        if limit.maxvalue > -1:
            newvalue -= limit.maxvalue
            if newvalue == 0:
                return
        remain = ol.maxvalue - ol.curvalue
        if newvalue > remain:
            raise UnsifficientResource(ol)
        ol.maxvalue -= newvalue
        ol.save()

    def save(self):
        from modoboa.lib.permissions import get_object_owner

        owner = get_object_owner(self.account)
        for ltpl in limits_tpl:
            if not self.cleaned_data.has_key(ltpl[0]):
                continue
            l = self.account.limitspool.limit_set.get(name=ltpl[0])
            if not owner.is_superuser:
                self.allocate_from_pool(l, owner.limitspool)
            l.maxvalue = self.cleaned_data[ltpl[0]]
            l.save()

    
