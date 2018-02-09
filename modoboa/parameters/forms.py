# -*- coding: utf-8 -*-

"""Parameters forms."""

from __future__ import unicode_literals

from django import forms

from modoboa.lib import db_utils, form_utils


class GenericParametersForm(forms.Form):
    """Base class for parameter forms.

    Each extension has the possibility to define global parameters.
    """
    app = None
    visibility_rules = None

    def __init__(self, *args, **kwargs):
        """Constructor."""
        if self.app is None:
            raise NotImplementedError

        kwargs["prefix"] = self.app
        load_values_from_db = kwargs.pop("load_values_from_db", True)
        super(GenericParametersForm, self).__init__(*args, **kwargs)

        self.visirules = {}
        if self.visibility_rules is not None:
            for key, rule in list(self.visibility_rules.items()):
                field, value = rule.split("=")
                visibility = {
                    "field": "id_%s-%s" % (self.app, field), "value": value
                }
                self.visirules["%s-%s" % (self.app, key)] = visibility

        if not args and load_values_from_db:
            self._load_initial_values()

    def _load_initial_values(self):
        raise NotImplementedError

    @staticmethod
    def has_access(**kwargs):
        return True

    def save(self):
        raise NotImplementedError


class AdminParametersForm(GenericParametersForm):
    """Base form to declare admin level parameters."""

    def __init__(self, *args, **kwargs):
        """Store LocalConfig instance."""
        self.localconfig = kwargs.pop("localconfig", None)
        super(AdminParametersForm, self).__init__(*args, **kwargs)

    def _load_initial_values(self):
        """Load form initial values from database."""
        condition = (
            not db_utils.db_table_exists("core_localconfig") or
            not self.localconfig)
        if condition:
            return
        values = self.localconfig.parameters.get_values(app=self.app)
        for key, value in values:
            self.fields[key].initial = value

    def save(self):
        """Save parameters to database."""
        parameters = {}
        for name, value in list(self.cleaned_data.items()):
            if isinstance(self.fields[name], form_utils.SeparatorField):
                continue
            parameters[name] = value
        self.localconfig.parameters.set_values(parameters, app=self.app)

    def to_django_settings(self):
        """Inject parameters into django settings module."""
        pass


class UserParametersForm(GenericParametersForm):
    """Base form to declare user level parameters."""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super(UserParametersForm, self).__init__(*args, **kwargs)

    def _load_initial_values(self):
        """Load initial values from User instance."""
        if not db_utils.db_table_exists("core_localconfig"):
            return
        if self.user is None:
            return
        parameters = self.user.parameters.get_values(self.app)
        for parameter, value in parameters:
            self.fields[parameter].initial = value

    def save(self):
        """Save new values."""
        parameters = {}
        for name, value in list(self.cleaned_data.items()):
            if isinstance(self.fields[name], form_utils.SeparatorField):
                continue
            parameters[name] = value
        self.user.parameters.set_values(parameters, app=self.app)
