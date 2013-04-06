# coding: utf-8
"""
This interface provides a simple way to declare and store parameters
in Modoboa's database.

Core components or extensions can register their own parameters, which
will be available and modifiable directly from the web interface.

Only super users will be able to access this part of the web interface.
"""

import inspect
import re
import copy
from django import forms
from exceptions import ModoboaException


_params = {'A': {}, 'U': {}}


class NotDefined(ModoboaException):
    def __init__(self, app, name):
        self.app = app
        self.name = name

    def __str__(self):
        return "Application '%s' and/or parameter '%s' not defined" \
            % (self.app, self.name)


class GenericParametersForm(forms.Form):
    app = None

    def __init__(self, *args, **kwargs):
        if self.app is None:
            raise NotImplementedError

        kwargs["prefix"] = self.app
        super(GenericParametersForm, self).__init__(*args, **kwargs)

        self.visirules = {}
        for param in self.fields.keys():
            fname = "visibility_%s" % param
            if not hasattr(self, fname):
                continue
            field, value = getattr(self, fname)().split("=")
            visibility = {"field": "id_%s-%s" % (self.app, field), "value": value}
            self.visirules["%s-%s" % (self.app, param)] = visibility

        if not args:
            self._load_initial_values()

    def _load_initial_values(self):
        raise NotImplementedError

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

    def save(self):
        raise NotImplementedError


class AdminParametersForm(GenericParametersForm):
    def _load_initial_values(self):
        from models import Parameter

        for name in self.fields.keys():
            fullname = "%s.%s" % (self.app, name.upper())
            try:
                p = Parameter.objects.get(name=fullname)
            except Parameter.DoesNotExist:
                continue
            self.fields[name].initial = p.value

    def save(self):
        from models import Parameter
        from modoboa.lib.formutils import SeparatorField

        for name, value in self.cleaned_data.items():
            if type(self.fields[name]) is SeparatorField:
                continue
            fullname = "%s.%s" % (self.app, name.upper())
            try:
                p = Parameter.objects.get(name=fullname)
            except Parameter.DoesNotExist:
                p = Parameter()
                p.name = fullname
            self._save_parameter(p, name, value)


class UserParametersForm(GenericParametersForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user") if "user" in kwargs else None
        super(UserParametersForm, self).__init__(*args, **kwargs)

    def _load_initial_values(self):
        if self.user is None:
            return
        from models import UserParameter

        for name in self.fields.keys():
            fullname = "%s.%s" % (self.app, name.upper())
            try:
                p = UserParameter.objects.get(user=self.user, name=fullname)
            except UserParameter.DoesNotExist:
                continue
            self.fields[name].initial = p.value

    @staticmethod
    def has_access(user):
        return True

    def save(self):
        from models import UserParameter
        from modoboa.lib.formutils import SeparatorField

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
    """Register a form class containing parameters

    formclass must inherit from ``AdminParametersForm`` of
    ``UserParametersForm``.

    :param formclass: a form class
    :param label: 
    """
    from models import Parameter
    from modoboa.lib.formutils import SeparatorField

    if issubclass(formclass, AdminParametersForm):
        level = 'A'
    elif issubclass(formclass, UserParametersForm):
        level = 'U'
    else:
        raise RuntimeError("Unknown parameter class")
    _params[level][formclass.app] = {"label": label, "form": formclass, "defaults": {}}
    form = formclass()
    for name, field in form.fields.items():
        if type(field) is SeparatorField:
            continue
        _params[level][formclass.app]["defaults"][name.upper()] = field.initial


def unregister(app=None):
    """Unregister an application

    All parameters associated to this application will also be
    removed.

    :param app: the application's name (string)
    """
    if app is None:
        app = __guess_extension()
    for lvlparams in _params.values():
        if app in lvlparams:
            del lvlparams[app]


def __is_defined(app, level, name):
    if not level in ['A', 'U'] \
        or not app in _params[level] \
        or not name in _params[level][app]["defaults"]:
        raise NotDefined(app, name)


def __guess_extension():
    """Tries to guess the application's name by inspecting the stack

    :return: a string or None
    """
    modname = inspect.getmodule(inspect.stack()[2][0]).__name__
    m = re.match("(?:modoboa\.)?(?:extensions\.)?([^\.$]+)", modname)
    if m:
        return m.group(1)
    return None


def save_admin(name, value, app=None):
    from models import Parameter

    if app is None:
        app = __guess_extension()
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
    from models import UserParameter

    if app is None:
        app = __guess_extension()
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
    """Return an administrative parameter

    A ``NotDefined`` exception if the parameter doesn't exist.

    :param name: the parameter's name
    :param app: the application owning the parameter
    :return: the corresponding value as a string
    """
    from models import Parameter

    if app is None:
        app = __guess_extension()
    try:
        __is_defined(app, "A", name)
    except NotDefined:
        if raise_error:
            raise
        return None
    try:
        p = Parameter.objects.get(name="%s.%s" % (app, name))
    except Parameter.DoesNotExist:
        return _params["A"][app]["defaults"][name]
    return p.value.decode("unicode_escape")


def get_user(user, name, app=None):
    """Return a parameter for a specific user

    A ``NotDefined`` exception if the parameter doesn't exist.

    :param ``User`` user: the desired user
    :param name: the parameter's name
    :param app: the application owning the parameter
    :return: the corresponding value as a string
    """
    from models import UserParameter

    if app is None:
        app = __guess_extension()
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
    for formdef in _params['A'].values():
        yield {"label": formdef["label"], "form": formdef["form"](*args, **kwargs)}


def get_user_forms(user, *args, **kwargs):
    kwargs["user"] = user
    def realfunc():
        for formdef in _params['U'].values():
            if not formdef["form"].has_access(user):
                continue
            yield {"label": formdef["label"], "form": formdef["form"](*args, **kwargs)}

    return realfunc


def get_parameter_form(level, name, app=None):
    """Return the form containing a specific parameter

    :param string level: associated level
    :param string name: paremeter's name
    :param string app: parameter's application
    :return: a form class
    """
    if app is None:
        app = __guess_extension()
    __is_defined(app, level, name)
    return _params[level][app]["form"]
