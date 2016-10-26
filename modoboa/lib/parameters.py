# coding: utf-8

"""
This interface provides a simple way to declare and store parameters
in Modoboa's database.

Core components or extensions can register their own parameters, which
will be available and modifiable directly from the web interface.

Only super users will be able to access this part of the web interface.
"""

from django import forms

from modoboa.core import parameters as core_parameters
from modoboa.lib import events
from modoboa.lib import signals
from modoboa.lib.sysutils import guess_extension_name

from . import db_utils
from . import form_utils


_params = {'A': {}, 'U': {}}


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
            for key, rule in self.visibility_rules.items():
                field, value = rule.split("=")
                visibility = {
                    "field": "id_%s-%s" % (self.app, field), "value": value
                }
                self.visirules["%s-%s" % (self.app, key)] = visibility

        if not args and load_values_from_db:
            self._load_initial_values()

    def _load_initial_values(self):
        raise NotImplementedError

    def _decode_value(self, value):
        return value.decode('unicode_escape').replace('\\r\\n', '\n')

    def _load_extra_parameters(self, level):
        params = events.raiseDictEvent('GetExtraParameters', self.app, level)
        for pname, pdef in params.items():
            self.fields[pname] = pdef

    def _save_parameter(self, p, name, value):
        if p.value == value:
            return
        name = name.lower()
        if hasattr(self, "update_%s" % name):
            getattr(self, "update_%s" % name)(value)
        if type(value) is unicode:
            p.value = value.encode("unicode_escape").strip()
        else:
            p.value = str(value)
        p.save()

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
        for name, value in self.cleaned_data.items():
            if type(self.fields[name]) is form_utils.SeparatorField:
                continue
            parameters[name] = value
        self.localconfig.parameters.set_values(parameters, app=self.app)

    def to_django_settings(self):
        """Inject parameters into django settings module."""
        pass

    def get_current_values(self):
        """Return current values from the database."""
        values = {}
        for key in self.fields.keys():
            try:
                values[key] = get_admin(key.upper(), app=self.app)
            except core_parameters.NotDefined:
                pass
        return values


class UserParametersForm(GenericParametersForm):

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user") if "user" in kwargs else None
        super(UserParametersForm, self).__init__(*args, **kwargs)

    def _load_initial_values(self):
        if not db_utils.db_table_exists("lib_userparameter"):
            return
        if self.user is None:
            return
        from .models import UserParameter

        names = [
            "%s.%s" % (self.app, name.upper()) for name in self.fields.keys()
        ]
        for p in UserParameter.objects.filter(user=self.user, name__in=names):
            self.fields[p.shortname].initial = self._decode_value(p.value)

    def save(self):
        from .models import UserParameter
        from modoboa.lib.form_utils import SeparatorField

        for name, value in self.cleaned_data.items():
            if type(self.fields[name]) is SeparatorField:
                continue
            fullname = "%s.%s" % (self.app, name.upper())
            try:
                p = UserParameter.objects.get(user=self.user, name=fullname)
            except UserParameter.DoesNotExist:
                p = UserParameter()
                p.user = self.user
                p.name = fullname
            self._save_parameter(p, name, value)


def register(formclass, label):
    """Register a form class containing parameters.

    formclass must inherit from ``AdminParametersForm`` or
    ``UserParametersForm``.

    :param formclass: a form class
    :param string label: the label to display in parameters or settings pages
    """
    if issubclass(formclass, AdminParametersForm):
        level = "admin"
    elif issubclass(formclass, UserParametersForm):
        level = "user"
    else:
        raise RuntimeError("Unknown parameter class")
    core_parameters.registry.add(level, formclass, label)


def unregister(app=None):
    """Unregister an application

    All parameters associated to this application will also be
    removed.

    :param app: the application's name (string)
    """
    if app is None:
        app = guess_extension_name()
    for lvlparams in _params.values():
        if app in lvlparams:
            del lvlparams[app]


def __is_defined(app, level, name):
    not_defined = (
        level not in ['A', 'U'] or
        app not in _params[level] or
        name not in _params[level][app]["defaults"]
    )
    if not_defined:
        raise NotDefined(app, name)


def save_admin(name, value, app=None):
    """Set a new value for a given parameter."""
    from .models import Parameter

    if app is None:
        app = guess_extension_name()
    __is_defined(app, 'A', name)
    fullname = "%s.%s" % (app, name)
    try:
        p = Parameter.objects.get(name=fullname)
    except Parameter.DoesNotExist:
        p = Parameter()
        p.name = fullname
        p.value = None
    f = get_parameter_form('A', name, app)
    f()._save_parameter(p, name, value)


def save_user(user, name, value, app=None):
    from .models import UserParameter

    if app is None:
        app = guess_extension_name()
    __is_defined(app, 'U', name)
    fullname = "%s.%s" % (app, name)
    try:
        p = UserParameter.objects.get(user=user, name=fullname)
    except UserParameter.DoesNotExist:
        p = UserParameter()
        p.user = user
        p.name = fullname
    f = get_parameter_form('U', name, app)
    f()._save_parameter(p, name, value)


def get_admin(name, app=None, raise_error=True):
    """Return an administrative parameter.

    A ``NotDefined`` exception if the parameter doesn't exist.

    :param name: the parameter's name
    :param app: the application owning the parameter
    :return: the corresponding value as a string
    """
    # FIXME: deprecate this function
    request = signals.get_request()
    if request:
        localconfig = request.localconfig
    else:
        from modoboa.core import models as core_models
        localconfig = core_models.LocalConfig.objects.first()
    if app is None:
        app = guess_extension_name()
    return localconfig.parameters.get_value(
        name, app=app, raise_exception=raise_error)


def get_user(user, name, app=None, raise_error=True):
    """Return a parameter for a specific user

    A ``NotDefined`` exception if the parameter doesn't exist.

    :param ``User`` user: the desired user
    :param name: the parameter's name
    :param app: the application owning the parameter
    :return: the corresponding value as a string
    """
    from .models import UserParameter

    if app is None:
        app = guess_extension_name()
    try:
        __is_defined(app, "U", name)
    except NotDefined:
        if raise_error:
            raise
        return None
    try:
        p = UserParameter.objects.get(user=user, name="%s.%s" % (app, name))
    except UserParameter.DoesNotExist:
        return _params["U"][app]["defaults"][name]
    return p.value.decode("unicode_escape")


def get_admin_forms(*args, **kwargs):
    """Get all admin level forms.

    Generates an instance of each declared form.
    """
    return core_parameters.registry.get_forms(
        "admin", *args, **kwargs)


def get_user_forms(user, *args, **kwargs):
    """Return an instance of each user-level forms."""
    kwargs.update({"user": user, "first_app": "general"})
    return core_parameters.registry.get_forms(
        "user", *args, **kwargs)


def get_parameter_form(level, name, app=None):
    """Return the form containing a specific parameter

    :param string level: associated level
    :param string name: paremeter's name
    :param string app: parameter's application
    :return: a form class
    """
    if app is None:
        app = guess_extension_name()
    __is_defined(app, level, name)
    return _params[level][app]["form"]


def apply_to_django_settings():
    for form in get_admin_forms():
        form["form"].to_django_settings()
