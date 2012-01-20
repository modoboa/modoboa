# -*- coding: utf-8 -*-

"""
:mod:`events` --- simple events handling
----------------------------------------

This module provides a simple way of managing events between Modoboa
core application and additional components.

"""
from functools import wraps
import inspect
import re

events = [
    "CanCreateDomain",
    "CreateDomain",
    "DeleteDomain",

    "CanCreateDomainAlias",
    "DomainAliasCreated",
    "DomainAliasDeleted",

    "CanCreateMailbox",
    "CreateMailbox",
    "DeleteMailbox",
    "ModifyMailbox",

    "CanCreateMailboxAlias",
    "MailboxAliasCreated",
    "MailboxAliasDeleted",

    "DomainAdminCreated",

    "PasswordChange",
    
    "UserMenuDisplay",
    "AdminMenuDisplay",
    
    "PermsGetTables",
    "PermsGetClass",
    
    "ExtEnabled",
    "ExtDisabled",

    "UserLogin",
    "UserLogout",
    
    "GetAnnouncement",

    "AdminFooterDisplay",
    ]

callbacks = {}

def register(event, callback):
    """Register a plugin callback for a specific event

    The event must be declared in this module.

    :param event: the event to listen to
    :param callback: a function to execute when the event is raised
    """
    if not event in events:
        return 0
    if not event in callbacks.keys():
        callbacks[event] = []
    if not callback in callbacks[event]:
        callbacks[event].append(callback)
    return 1

class observe(object):
    """Event observing decorator

    Automatically register the decorated function to observe the given
    event. If the decorated function is located into an extension, we
    check before each call if the extension is enabled or not. If
    that's not the case, the callback is not called.

    .. note::

        That's not a really optimized behaviour but I haven't found
        another solution to achieve that feature.

    :param evtname: the event's name
    """
    def __init__(self, evtname):
        self.evtname = evtname

    def __guess_extension_name(self, modname):
        if modname.startswith('modoboa.extensions'):
            m = re.match(r'modoboa\.extensions\.([^\.]+)', modname)
            if m:
                return m.group(1)
        return None

    def __call__(self, f):
        modname = inspect.getmodule(inspect.stack()[1][0]).__name__
        extname = self.__guess_extension_name(modname)
        @wraps(f)
        def wrapped_f(*args):
            if extname:
                from modoboa.admin.models import Extension
                try:
                    ext = Extension.objects.get(name=extname)
                except Extension.DoesNotExist:
                    return []
                if not ext.enabled:
                    return []
            return f(*args)

        register(self.evtname, wrapped_f)
        return wrapped_f

def unregister(event, callback):
    """Unregister a callback for a specific event

    :param event: the targeted event
    :param callback: the callback to remove
    """
    if not event in events:
        return False
    if not callbacks.has_key(event):
        return False
    try:
        callbacks[event].remove(callback)
    except ValueError:
        pass

def raiseEvent(event, *args):
    """Raise a specific event

    Any additional keyword argument will be passed to registered
    callbacks.

    :param event: the event to raise
    """
    if not event in events or not event in callbacks.keys():
        return 0
    for callback in callbacks[event]:
        callback(*args)
    return 1

def raiseQueryEvent(event, *args):
    """Raise a specific event and wait for answers from callbacks

    Any additional keyword argument will be passed to registered
    callbacks. Callback answers are returned as a list.

    :param event: the event to raise
    """
    result = []
    if not event in events or not event in callbacks.keys():
        return result
    for callback in callbacks[event]:
        result += callback(*args)
    return result
