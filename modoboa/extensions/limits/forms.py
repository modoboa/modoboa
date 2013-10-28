# coding: utf-8
from django import forms
from django.utils.translation import ugettext as _, ugettext_lazy
from modoboa.lib import parameters
from .models import LimitTemplates
from .lib import BadLimitValue, UnsufficientResource


class ResourcePoolForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.account = None
        if "instance" in kwargs:
            self.account = kwargs["instance"]
            del kwargs["instance"]
        super(ResourcePoolForm, self).__init__(*args, **kwargs)
        for tpl in LimitTemplates().templates:
            if len(tpl) > 3 and self.account is not None and self.account.group != tpl[3]:
                continue
            self.fields[tpl[0]] = forms.IntegerField(
                label=tpl[1], help_text=tpl[2]
            )
        if hasattr(self, "account"):
            self.load_from_user(self.account)

    def check_limit_value(self, lname):
        if self.cleaned_data[lname] < -1:
            raise forms.ValidationError(_("Invalid limit"))
        return self.cleaned_data[lname]

    def clean(self):
        cleaned_data = super(ResourcePoolForm, self).clean()
        for lname in self.fields.keys():
            if not lname in self._errors and cleaned_data[lname] < -1:
                self._errors[lname] = self.error_class([_('Invalid limit')])
                del cleaned_data[lname]
        return cleaned_data

    def load_from_user(self, user):
        for lname in self.fields.keys():
            self.fields[lname].initial = user.limitspool.getmaxvalue(lname)
            # The following lines will become useless in a near
            # future.
            if self.fields[lname].initial == -2:
                self.fields[lname].initial = parameters.get_admin("DEFLT_%s" % lname.upper())

    def allocate_from_pool(self, limit, pool):
        """Allocate resource using an existing pool.

        When a reseller creates a domain administrator, he generally
        assigns him resource to create new objetcs. As a reseller may
        also be limited, the resource he gives is taken from its own
        pool.
        """
        ol = pool.get_limit(limit.name)
        if ol.maxvalue == -2:
            raise BadLimitValue(_("Your resources are not initialized yet"))
        newvalue = self.cleaned_data[limit.name]
        if newvalue == -1 and ol.maxvalue != -1:
            raise BadLimitValue(
                _("You're not allowed to define unlimited values")
            )

        if limit.maxvalue > -1:
            newvalue -= limit.maxvalue
            if newvalue == 0:
                return
        remain = ol.maxvalue - ol.curvalue
        if newvalue > remain:
            raise UnsufficientResource(ol)
        ol.maxvalue -= newvalue
        ol.save()

    def save(self):
        from modoboa.lib.permissions import get_object_owner

        owner = get_object_owner(self.account)
        for ltpl in LimitTemplates().templates:
            if not ltpl[0] in self.cleaned_data:
                continue
            l = self.account.limitspool.limit_set.get(name=ltpl[0])
            if not owner.is_superuser:
                self.allocate_from_pool(l, owner.limitspool)
            l.maxvalue = self.cleaned_data[ltpl[0]]
            l.save()
