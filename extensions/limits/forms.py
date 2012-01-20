# coding: utf-8

from django import forms
from django.utils.translation import ugettext_noop as _
from django.contrib.auth.models import User, Group
from modoboa.admin.forms import UserForm, UserWithPasswordForm
from models import *

class ResellerForm(UserForm):
    def __init__(self, *args, **kwargs):
        super(ResellerForm, self).__init__(*args, **kwargs)
        del self.fields["createmb"]

    def save(self, commit=True, group=None):
        user = super(ResellerForm, self).save(commit, group)
        if commit:
            try:
                pool = user.limitspool
            except LimitsPool.DoesNotExist:
                pool = LimitsPool()
                pool.user = user
                print pool.user
                pool.save()
                
                for lname in reseller_limits_tpl:
                    l = Limit()
                    l.name = lname
                    l.pool = pool
                    l.save()

        return user

class ResellerWithPasswordForm(ResellerForm, UserWithPasswordForm):
    pass

class ResellerPoolForm(forms.Form):
    domains_limit = forms.IntegerField(ugettext_noop("Max domains"),
        help_text=ugettext_noop("Maximum number of domains that can be created by this user"))
    domain_aliases_limit = forms.IntegerField(ugettext_noop("Max domain aliases"),
        help_text=ugettext_noop("Maximum number of domain aliases that can be created by this user"))
    mailboxes_limit = forms.IntegerField(ugettext_noop("Max mailboxes"),
        help_text=ugettext_noop("Maximum number of mailboxes that can be created by this user"))
    mailbox_aliases_limit = forms.IntegerField(ugettext_noop("Max mailbox aliases"),
        help_text=ugettext_noop("Maximum number of mailbox aliases that can be created by this user"))

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
        for l in reseller_limits_tpl:
            self.fields[l].initial = user.limitspool.getmaxvalue(l)

    def save_new_limits(self, pool):
        for lname in reseller_limits_tpl:
            l = pool.limit_set.get(name=lname)
            l.maxvalue = self.cleaned_data[lname]
            l.save()

    
