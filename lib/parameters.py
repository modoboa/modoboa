# -*- coding: utf-8 -*-

import string
from mailng.admin.models import Parameter

"""
This interface provides a simple way to declare and store parameters
in MailNG's database.

Core components or extensions can register their own parameters, which
will be available and modifiable directly from the web interface.

Only super users will be able to acces this part of the web interface.
"""

_params = {}

class NotDefined(Exception):
    def __init__(self, app, name):
        self.app = app
        self.name = name

    def __str__(self):
        return "Application '%s' and/or parameter '%s' not defined" % (self.app,
                                                                       self.name)

def register(app, name, type="string", deflt=None, help=None, **kwargs):
    """Register a new parameter.

    app corresponds to a core component (admin, main) or an extension.
    """
    if not app in _params.keys():
        _params[app] = {}
    _params[app][name] = {"type" : type, "default" : deflt, "help" : help}

def save(app, name, value):
    if not app in _params.keys() or not name in _params[app].keys():
        raise NotDefined(app, name)
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

def get(app, name):
    if not app in _params.keys() or not name in _params[app].keys():
        raise NotDefined(app, name)
    try:
        p = Parameter.objects.get(name="%s.%s" % (app, name))
    except Parameter.DoesNotExist:
        return _params[app][name]["default"]
    return p.value
