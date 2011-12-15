# -*- coding: utf-8 -*-

import string
import inspect
import re

"""
This interface provides a simple way to declare and store parameters
in Modoboa's database.

Core components or extensions can register their own parameters, which
will be available and modifiable directly from the web interface.

Only super users will be able to access this part of the web interface.
"""

_params = {}
_params_order = {}
_levels = {'A' : 'admin', 'U' : 'user'}

class NotDefined(Exception):
    def __init__(self, app, name):
        self.app = app
        self.name = name

    def __str__(self):
        return "Application '%s' and/or parameter '%s' not defined" \
            % (self.app, self.name)

def __is_defined(app, level, name):
    if not level in _levels.keys() \
            or not app in _params.keys() \
            or not name in _params[app][level].keys():
        raise NotDefined(app, name)

def __register(app, level, name, **kwargs):
    """Register a new parameter.

    ``app`` corresponds to a core component (admin, main) or to an
    extension.

    :param name: the application's name
    :param level: the level this parameter is available from
    :param name: the parameter's name
    """ 
    if not app in _params.keys():
        _params[app] = {}
        _params_order[app] = {}
        for lvl in _levels.keys():
            _params[app][lvl] = {}
            _params_order[app][lvl] = []
    if not level in _levels.keys():
        return
    if _params[app][level].has_key(name):
        return
    _params[app][level][name] = {}
    _params_order[app][level] += [name]
    for k, v in kwargs.iteritems():
        _params[app][level][name][k] = v

def __update(app, level, name, **kwargs):
    """Update a parameter's definition

    :param app: the application's name
    :param level: the level this parameter is available from
    :param name: the parameter's name
    """
    if not app in _params.keys() or not level in _levels.keys() \
            or not _params[app][level].has_key(name):
        return
    for k, v in kwargs.iteritems():
        _params[app][level][name][k] = v

def __guess_extension():
    """Tries to guess the application's name by inspecting the stack

    :return: a string or None
    """
    modname = inspect.getmodule(inspect.stack()[2][0]).__name__
    m = re.match("(?:modoboa\.)?(?:extensions\.)?([^\.$]+)", modname)
    if m:
        return m.group(1)
    return None

def register_admin(name, **kwargs):
    """Register a new parameter (admin level)

    Each parameter is associated to one application. If no application
    is provided, the function tries to guess the appropriate one.

    :param name: the parameter's name
    """
    if kwargs.has_key("app"):
        app = kwargs["app"]
        del kwargs["app"]
    else:
        app = __guess_extension()
    return __register(app, 'A', name, **kwargs)

def update_admin(name, **kwargs):
    """Update a parameter's definition (admin level)

    Each parameter is associated to one application. If no application
    is provided, the function tries to guess the appropriate one.

    :param name: the parameter's name
    """
    if kwargs.has_key("app"):
        app = kwargs["app"]
        del kwargs["app"]
    else:
        app = __guess_extension()
    return __update(app, 'A', name, **kwargs)

def register_user(name, **kwargs):
    if kwargs.has_key("app"):
        app = kwargs["app"]
        del kwargs["app"]
    else:
        app = __guess_extension()
    return __register(app, 'U', name, **kwargs)

def unregister_app(app):
    if not _params.has_key(app):
        return False
    del _params[app]
    return True

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
    if p.value != value:
        p.value = str(value).encode("string_escape").strip()
        p.save()
    return True

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
    if p.value != value:
        p.value = str(value).encode("string_escape").strip()
        p.save()
    return True

def get_admin(name, app=None):
    from models import Parameter

    if app is None:
        app = __guess_extension()
    __is_defined(app, "A", name)
    try:
        p = Parameter.objects.get(name="%s.%s" % (app, name))
    except Parameter.DoesNotExist:
        return _params[app]["A"][name]["deflt"]
    return p.value.decode("string_escape")

def get_user(user, name, app=None):
    from models import UserParameter

    if app is None:
        app = __guess_extension()
    __is_defined(app, "U", name)
    try:
        p = UserParameter.objects.get(user=user, name="%s.%s" % (app, name))
    except UserParameter.DoesNotExist:
        return _params[app]["U"][name]["deflt"]
    return p.value.decode("string_escape")
