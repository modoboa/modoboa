# -*- coding: utf-8 -*-

"""Custom forms."""

from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext as _

from modoboa.lib.permissions import get_object_owner
from . import utils
from .lib import allocate_resources_from_user


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
        for lname in list(self.fields.keys()):
            if cleaned_data[lname] < -1:
                self.add_error(lname, _("Invalid limit"))
        return cleaned_data

    def load_from_user(self, user):
        """Load limit values from given user."""
        for fieldname in list(self.fields.keys()):
            lname = fieldname.replace("_limit", "")
            self.fields[fieldname].initial = (
                user.userobjectlimit_set.get(name=lname).max_value)

    def save(self):
        owner = get_object_owner(self.account)
        for name, _definition in utils.get_user_limit_templates():
            fieldname = "{}_limit".format(name)
            if fieldname not in self.cleaned_data:
                continue
            limit = self.account.userobjectlimit_set.get(name=name)
            if not owner.is_superuser:
                allocate_resources_from_user(
                    limit, owner, self.cleaned_data[fieldname])
            limit.max_value = self.cleaned_data[fieldname]
            limit.save(update_fields=["max_value"])


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
        for fieldname in list(self.fields.keys()):
            lname = fieldname.replace("_limit", "")
            self.fields[fieldname].initial = (
                self.domain.domainobjectlimit_set.get(name=lname).max_value)

    def clean(self):
        """Ensure limit values are correct."""
        cleaned_data = super(DomainLimitsForm, self).clean()
        if self.errors:
            return cleaned_data
        for lname in list(self.fields.keys()):
            if cleaned_data[lname] < -1:
                self.add_error(lname, _("Invalid limit"))
        return cleaned_data

    def save(self, user, **kwargs):
        """Set limits."""
        for name, _definition in utils.get_domain_limit_templates():
            fieldname = "{}_limit".format(name)
            if fieldname not in self.cleaned_data:
                continue
            limit = self.domain.domainobjectlimit_set.get(name=name)
            limit.max_value = self.cleaned_data[fieldname]
            limit.save()
