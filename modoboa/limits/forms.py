# coding: utf-8

"""Custom forms."""

from django import forms
from django.utils.translation import ugettext as _

from modoboa.lib.permissions import get_object_owner

from .lib import BadLimitValue, UnsufficientResource
from . import utils


class ResourcePoolForm(forms.Form):
    """Dynamic form to display user limits."""

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop("instance", None)
        super(ResourcePoolForm, self).__init__(*args, **kwargs)
        for name, tpl in utils.get_user_limit_templates():
            if "required_role" in tpl:
                condition = (
                    self.account is not None and
                    self.account.role != tpl["required_role"]
                )
                if condition:
                    continue
            self.fields["{}_limit".format(name)] = forms.IntegerField(
                label=tpl["label"], help_text=tpl["help"]
            )
        if self.account:
            self.load_from_user(self.account)

    def clean(self):
        """Ensure limit values are correct."""
        cleaned_data = super(ResourcePoolForm, self).clean()
        if self.errors:
            return cleaned_data
        for lname in self.fields.keys():
            if cleaned_data[lname] < -1:
                self.add_error(lname, _("Invalid limit"))
        return cleaned_data

    def load_from_user(self, user):
        """Load limit values from given user."""
        for fieldname in self.fields.keys():
            lname = fieldname.replace("_limit", "")
            self.fields[fieldname].initial = (
                user.userobjectlimit_set.get(name=lname).max_value)

    def allocate_from_user(self, limit, user):
        """Allocate resource using an existing user.

        When a reseller creates a domain administrator, he generally
        assigns him resource to create new objetcs. As a reseller may
        also be limited, the resource he gives is taken from its own
        pool.
        """
        ol = user.userobjectlimit_set.get(name=limit.name)
        fieldname = "{}_limit".format(limit.name)
        newvalue = self.cleaned_data[fieldname]
        if newvalue == -1 and ol.max_value != -1:
            raise BadLimitValue(
                _("You're not allowed to define unlimited values")
            )

        if limit.max_value > -1:
            newvalue -= limit.max_value
            if newvalue == 0:
                return
        remain = ol.max_value - ol.current_value
        if newvalue > remain:
            raise UnsufficientResource(ol)
        ol.max_value -= newvalue
        ol.save()

    def save(self):
        owner = get_object_owner(self.account)
        for name, ltpl in utils.get_user_limit_templates():
            fieldname = "{}_limit".format(name)
            if fieldname not in self.cleaned_data:
                continue
            l = self.account.userobjectlimit_set.get(name=name)
            if not owner.is_superuser:
                self.allocate_from_user(l, owner)
            l.max_value = self.cleaned_data[fieldname]
            l.save()


class DomainLimitsForm(forms.Form):
    """Per-domain limits form."""

    def __init__(self, *args, **kwargs):
        """Define limits as fields."""
        self.domain = kwargs.pop("instance", None)
        super(DomainLimitsForm, self).__init__(*args, **kwargs)
        for name, tpl in utils.get_domain_limit_templates():
            self.fields["{}_limit".format(name)] = forms.IntegerField(
                label=tpl["label"], help_text=tpl["help"]
            )
        if not self.domain:
            return
        for fieldname in self.fields.keys():
            lname = fieldname.replace("_limit", "")
            self.fields[fieldname].initial = (
                self.domain.domainobjectlimit_set.get(name=lname).max_value)

    def clean(self):
        """Ensure limit values are correct."""
        cleaned_data = super(DomainLimitsForm, self).clean()
        if self.errors:
            return cleaned_data
        for lname in self.fields.keys():
            if cleaned_data[lname] < -1:
                self.add_error(lname, _("Invalid limit"))
        return cleaned_data

    def save(self, user):
        """Set limits."""
        for name, ltpl in utils.get_domain_limit_templates():
            fieldname = "{}_limit".format(name)
            if fieldname not in self.cleaned_data:
                continue
            l = self.domain.domainobjectlimit_set.get(name=name)
            l.max_value = self.cleaned_data[fieldname]
            l.save()
