# -*- coding: utf-8 -*-

import string
from modoboa.lib.models import *

"""
This interface provides a simple way to declare and store parameters
in MailNG's database.

Core components or extensions can register their own parameters, which
will be available and modifiable directly from the web interface.

Only super users will be able to access this part of the web interface.
"""

_params = {}
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

def __register(app, level, name, type="string", deflt=None, help=None, **kwargs):
    """Register a new parameter.

    app corresponds to a core component (admin, main) or an extension.
    """
    if not app in _params.keys():
        _params[app] = {}
        for lvl in _levels.keys():
            _params[app][lvl] = {}
    if not level in _levels.keys():
        return
    _params[app][level][name] = {"type" : type, "default" : deflt, "help" : help}
    for k, v in kwargs.iteritems():
        _params[app][level][name][k] = v

def register_admin(app, name, **kwargs):
    return __register(app, 'A', name, **kwargs)

def register_user(app, name, **kwargs):
    return __register(app, 'U', name, **kwargs)

def unregister_app(app):
    if not _params.has_key(app):
        return False
    del _params[app]
    return True

def save_admin(app, name, value):
    __is_defined(app, 'A', name)

    fullname = "%s.%s" % (app, name)
    try:
        p = Parameter.objects.get(name=fullname)
    except Parameter.DoesNotExist:
        p = Parameter()
        p.name = fullname
    if p.value != value:
        p.value = value
        p.save()
    return True

def save_user(user, app, name, value):
    __is_defined(app, 'U', name)
    fullname = "%s.%s" % (app, name)
    try:
        p = UserParameter.objects.get(user=user, name=fullname)
    except UserParameter.DoesNotExist:
        p = UserParameter()
        p.user = user
        p.name = fullname
    if p.value != value:
        p.value = value
        p.save()
    return True

def get_admin(app, name):
    __is_defined(app, "A", name)
    try:
        p = Parameter.objects.get(name="%s.%s" % (app, name))
    except Parameter.DoesNotExist:
        return _params[app]["A"][name]["default"]
    return p.value

def get_user(user, app, name):
    __is_defined(app, "U", name)
    try:
        p = UserParameter.objects.get(user=user, name="%s.%s" % (app, name))
    except UserParameter.DoesNotExist:
        return _params[app]["U"][name]["default"]
    return p.value
